from __future__ import annotations
import numpy as np


def _segments(points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    points = np.ascontiguousarray(points, dtype=float)
    nxt = np.roll(points, -1, axis=0)
    return 0.5 * (points + nxt), nxt - points


def velocity_at_points(
    evaluation_points: np.ndarray,
    source_points: np.ndarray,
    gamma: float,
    epsilon: float,
    same_curve: bool = False,
    local_skip: int = 3,
) -> np.ndarray:
    evaluation_points = np.ascontiguousarray(evaluation_points, dtype=float)
    source_points = np.ascontiguousarray(source_points, dtype=float)
    mid, dl = _segments(source_points)
    out = np.zeros_like(evaluation_points)
    eps2 = float(epsilon) ** 2
    nsrc = len(source_points)
    for p, point in enumerate(evaluation_points):
        diff = point[None, :] - mid
        kernel = np.cross(dl, diff) / np.maximum(
            (np.einsum("ij,ij->i", diff, diff) + eps2)[:, None] ** 1.5,
            1e-300,
        )
        if same_curve:
            idx = np.arange(nsrc)
            cyc = np.minimum((p - idx) % nsrc, (idx - p) % nsrc)
            kernel[cyc <= max(int(local_skip), 0)] = 0.0
        out[p] = float(gamma) / (4.0 * np.pi) * kernel.sum(axis=0)
    return out


def link_velocity_batch(
    curves: list[np.ndarray],
    sign_matrix: np.ndarray,
    epsilon: float,
    local_skip: int = 3,
) -> list[np.ndarray]:
    curves = [np.ascontiguousarray(c, dtype=float) for c in curves]
    signs = np.ascontiguousarray(sign_matrix, dtype=float)
    sectors, components = signs.shape
    if components != len(curves):
        raise ValueError("sign_matrix has incompatible component count")
    outputs: list[np.ndarray] = []
    for i, target in enumerate(curves):
        unit = []
        for j, source in enumerate(curves):
            unit.append(velocity_at_points(target, source, 1.0, epsilon, i == j, local_skip))
        stacked = np.stack(unit, axis=0)  # (components, points, xyz)
        outputs.append(np.einsum("sc,cnk->snk", signs, stacked))
    return outputs


def gauss_linking_matrix(curves: list[np.ndarray]) -> np.ndarray:
    curves = [np.ascontiguousarray(c, dtype=float) for c in curves]
    out = np.zeros((len(curves), len(curves)), dtype=float)
    segs = [_segments(c) for c in curves]
    for i in range(len(curves)):
        ma, da = segs[i]
        for j in range(i + 1, len(curves)):
            mb, db = segs[j]
            diff = ma[:, None, :] - mb[None, :, :]
            cross = np.cross(da[:, None, :], db[None, :, :])
            num = np.einsum("ijk,ijk->ij", cross, diff)
            den = np.einsum("ijk,ijk->ij", diff, diff) ** 1.5
            value = float(np.sum(num / np.maximum(den, 1e-300)) / (4.0 * np.pi))
            out[i, j] = out[j, i] = value
    return out


def neumann_coupling_matrices(
    curves: list[np.ndarray],
    epsilons: np.ndarray,
    local_skip: int = 2,
) -> np.ndarray:
    curves = [np.ascontiguousarray(c, dtype=float) for c in curves]
    epsilons = np.ascontiguousarray(epsilons, dtype=float)
    segs = [_segments(c) for c in curves]
    out = np.zeros((len(epsilons), len(curves), len(curves)), dtype=float)
    for e, epsilon in enumerate(epsilons):
        for i, (mi, di) in enumerate(segs):
            for j in range(i, len(segs)):
                mj, dj = segs[j]
                diff = mi[:, None, :] - mj[None, :, :]
                den = np.sqrt(np.einsum("ijk,ijk->ij", diff, diff) + epsilon**2)
                dot = np.einsum("ik,jk->ij", di, dj)
                if i == j:
                    rows = np.arange(len(mi))[:, None]
                    cols = np.arange(len(mj))[None, :]
                    cyc = np.minimum((rows - cols) % len(mi), (cols - rows) % len(mi))
                    dot = np.where(cyc <= max(int(local_skip), 0), 0.0, dot)
                value = float(np.sum(dot / np.maximum(den, 1e-300)) / (8.0 * np.pi))
                out[e, i, j] = value
                out[e, j, i] = value
    return out



def tube_repulsion_energy(
    curves: list[np.ndarray],
    diameter: float,
    softness: float = 0.04,
    contact_margin: float = 0.0,
    local_skip_fraction: float = 0.035,
) -> float:
    curves = [np.ascontiguousarray(c, dtype=float) for c in curves]
    threshold = float(diameter) * (1.0 + float(contact_margin))
    softness_abs = max(float(softness) * float(diameter), 1e-12)
    total = 0.0
    count = 0
    for i, a in enumerate(curves):
        for j in range(i, len(curves)):
            b = curves[j]
            dist = np.linalg.norm(a[:, None, :] - b[None, :, :], axis=2)
            if i == j:
                n = len(a)
                rows = np.arange(n)[:, None]
                cols = np.arange(n)[None, :]
                cyc = np.minimum((rows-cols) % n, (cols-rows) % n)
                mask = (cyc > max(3, int(float(local_skip_fraction)*n))) & (rows < cols)
            else:
                mask = np.ones_like(dist, dtype=bool)
            z = (threshold - dist[mask]) / softness_abs
            values = np.logaddexp(0.0, z)
            total += float(np.sum(values*values))
            count += int(values.size)
    return total / max(count, 1)

def build_info() -> dict:
    return {
        "openmp": False,
        "openmp_max_threads": 1,
        "compiler": "python/numpy fallback",
        "cpp_standard": None,
        "kernel": "midpoint-segment Rosenhead-Moore Biot-Savart",
        "tube_repulsion_native": False,
        "neumann_symmetric_pair_reuse": True,
    }



def _arc_coordinates(points: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    points = np.ascontiguousarray(points, dtype=float)
    nxt = np.roll(points, -1, axis=0)
    seglen = np.linalg.norm(nxt - points, axis=1)
    vertex_s = np.concatenate(([0.0], np.cumsum(seglen[:-1])))
    mid_s = vertex_s + 0.5 * seglen
    return vertex_s, mid_s, float(seglen.sum())


def _cyclic_arc_distances(values: np.ndarray, reference: float, total_length: float) -> np.ndarray:
    d = np.abs(values - float(reference))
    return np.minimum(d, np.maximum(total_length - d, 0.0))


def link_velocity_batch_arc_exclusion(
    curves: list[np.ndarray],
    sign_matrix: np.ndarray,
    epsilon: float,
    exclusion_arc: float,
) -> list[np.ndarray]:
    curves = [np.ascontiguousarray(c, dtype=float) for c in curves]
    signs = np.ascontiguousarray(sign_matrix, dtype=float)
    sectors, components = signs.shape
    if components != len(curves):
        raise ValueError("sign_matrix has incompatible component count")
    if exclusion_arc < 0:
        raise ValueError("exclusion_arc must be non-negative")
    arc = [_arc_coordinates(c) for c in curves]
    segs = [_segments(c) for c in curves]
    outputs: list[np.ndarray] = []
    eps2 = float(epsilon) ** 2
    for i, target in enumerate(curves):
        unit = []
        for j, source in enumerate(curves):
            mid, dl = segs[j]
            field = np.zeros_like(target)
            for p, point in enumerate(target):
                diff = point[None, :] - mid
                kernel = np.cross(dl, diff) / np.maximum(
                    (np.einsum("ij,ij->i", diff, diff) + eps2)[:, None] ** 1.5,
                    1e-300,
                )
                if i == j:
                    vertex_s, mid_s, length = arc[j]
                    mask = _cyclic_arc_distances(mid_s, vertex_s[p], length) <= float(exclusion_arc)
                    kernel[mask] = 0.0
                field[p] = kernel.sum(axis=0) / (4.0 * np.pi)
            unit.append(field)
        outputs.append(np.einsum("sc,cnk->snk", signs, np.stack(unit, axis=0)))
    return outputs


def neumann_coupling_matrices_arc_exclusion(
    curves: list[np.ndarray],
    epsilons: np.ndarray,
    exclusion_arc: float,
) -> np.ndarray:
    curves = [np.ascontiguousarray(c, dtype=float) for c in curves]
    epsilons = np.ascontiguousarray(epsilons, dtype=float)
    if exclusion_arc < 0:
        raise ValueError("exclusion_arc must be non-negative")
    segs = [_segments(c) for c in curves]
    arcs = [_arc_coordinates(c) for c in curves]
    out = np.zeros((len(epsilons), len(curves), len(curves)), dtype=float)
    for e, epsilon in enumerate(epsilons):
        for i, (mi, di) in enumerate(segs):
            for j in range(i, len(segs)):
                mj, dj = segs[j]
                diff = mi[:, None, :] - mj[None, :, :]
                den = np.sqrt(np.einsum("ijk,ijk->ij", diff, diff) + epsilon**2)
                dot = np.einsum("ik,jk->ij", di, dj)
                if i == j:
                    _, mids, length = arcs[i]
                    d = np.abs(mids[:, None] - mids[None, :])
                    cyc = np.minimum(d, np.maximum(length - d, 0.0))
                    dot = np.where(cyc <= float(exclusion_arc), 0.0, dot)
                value = float(np.sum(dot / np.maximum(den, 1e-300)) / (8.0 * np.pi))
                out[e, i, j] = value
                out[e, j, i] = value
    return out
