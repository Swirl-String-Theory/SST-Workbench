from __future__ import annotations
import numpy as np

def _segments(points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    nxt = np.roll(points, -1, axis=0)
    return 0.5 * (points + nxt), nxt - points

def gauss_pair_integral(
    points_a: np.ndarray,
    points_b: np.ndarray,
    softening: float = 0.0,
    chunk: int = 256,
) -> float:
    ma, da = _segments(points_a)
    mb, db = _segments(points_b)
    total = 0.0
    eps2 = softening * softening
    for i0 in range(0, len(ma), chunk):
        i1 = min(i0 + chunk, len(ma))
        diff = ma[i0:i1, None, :] - mb[None, :, :]
        cross = np.cross(da[i0:i1, None, :], db[None, :, :])
        num = np.einsum("ijk,ijk->ij", cross, diff)
        den = (np.einsum("ijk,ijk->ij", diff, diff) + eps2) ** 1.5
        total += float(np.sum(num / np.maximum(den, 1e-30)))
    return total / (4.0 * np.pi)

def gauss_linking_matrix(curves: list[np.ndarray], chunk: int = 256) -> np.ndarray:
    m = len(curves)
    out = np.zeros((m, m), dtype=float)
    for i in range(m):
        for j in range(i + 1, m):
            value = gauss_pair_integral(curves[i], curves[j], 0.0, chunk)
            out[i, j] = out[j, i] = value
    return out

def writhe(points: np.ndarray, exclusion: int = 4, chunk: int = 256) -> float:
    mid, dl = _segments(points)
    n = len(mid)
    total = 0.0
    for i0 in range(0, n, chunk):
        i1 = min(i0 + chunk, n)
        diff = mid[i0:i1, None, :] - mid[None, :, :]
        cross = np.cross(dl[i0:i1, None, :], dl[None, :, :])
        num = np.einsum("ijk,ijk->ij", cross, diff)
        den = np.einsum("ijk,ijk->ij", diff, diff) ** 1.5
        ii = np.arange(i0, i1)[:, None]
        jj = np.arange(n)[None, :]
        cyclic = np.minimum((ii-jj) % n, (jj-ii) % n)
        mask = cyclic > exclusion
        total += float(np.sum(np.where(mask, num / np.maximum(den, 1e-30), 0.0)))
    return total / (4.0 * np.pi)

def topology_summary(curves: list[np.ndarray], compute_writhe: bool, chunk: int) -> dict:
    matrix = gauss_linking_matrix(curves, chunk=chunk)
    rounded = np.rint(matrix)
    upper = np.triu_indices(len(curves), 1)
    errors = np.abs(matrix[upper] - rounded[upper])
    wr = [writhe(c, chunk=chunk) for c in curves] if compute_writhe else []
    return {
        "linking_matrix": matrix,
        "linking_matrix_rounded": rounded.astype(int),
        "max_linking_integer_error": float(errors.max()) if errors.size else 0.0,
        "total_abs_pair_linking": float(np.sum(np.abs(matrix[upper]))),
        "signed_pair_linking_sum": float(np.sum(matrix[upper])),
        "component_writhe": wr,
    }
