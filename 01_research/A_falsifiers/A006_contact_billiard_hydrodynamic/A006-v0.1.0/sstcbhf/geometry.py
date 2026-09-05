from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy.interpolate import CubicSpline


@dataclass
class CurveGeometry:
    points: np.ndarray
    s: np.ndarray
    length: float
    ds: float
    tangents: np.ndarray
    curvature_vectors: np.ndarray
    curvature: np.ndarray
    normals: np.ndarray
    binormals: np.ndarray
    torsion: np.ndarray
    edge_lengths: np.ndarray
    edge_ratio: float
    edge_cv: float


class PeriodicCurve:
    """Periodic cubic spline over normalized arclength parameter s in [0,1)."""

    def __init__(self, points: np.ndarray):
        points = np.asarray(points, dtype=float)
        if points.ndim != 2 or points.shape[1] != 3 or len(points) < 8:
            raise ValueError("points must have shape (N,3), N>=8")
        edges = np.roll(points, -1, axis=0) - points
        lens = np.linalg.norm(edges, axis=1)
        if np.any(lens <= 0):
            raise ValueError("curve contains zero-length edge")
        u = np.concatenate([[0.0], np.cumsum(lens)])
        u /= u[-1]
        closed = np.vstack([points, points[0]])
        self._splines = [CubicSpline(u, closed[:, k], bc_type="periodic") for k in range(3)]
        self.length_polygon = float(np.sum(lens))

    def eval(self, s: np.ndarray | float, derivative: int = 0) -> np.ndarray:
        q = np.mod(np.asarray(s, dtype=float), 1.0)
        vals = np.stack([sp(q, derivative) for sp in self._splines], axis=-1)
        return vals

    def frame(self, s: np.ndarray | float):
        v = self.eval(s, 1)
        a = self.eval(s, 2)
        speed = np.linalg.norm(v, axis=-1, keepdims=True)
        speed = np.maximum(speed, 1e-15)
        t = v / speed
        va = np.sum(v * a, axis=-1, keepdims=True)
        kv = (a - v * va / (speed * speed)) / (speed * speed)
        kappa = np.linalg.norm(kv, axis=-1)
        n = np.zeros_like(kv)
        good = kappa > 1e-12
        n[good] = kv[good] / kappa[good, None]
        b = np.cross(t, n)
        bnorm = np.linalg.norm(b, axis=-1, keepdims=True)
        b = np.divide(b, np.maximum(bnorm, 1e-15), out=np.zeros_like(b), where=bnorm > 0)
        return t, kv, kappa, n, b


def resample_closed_curve(points: np.ndarray, samples: int, dense_factor: int = 8) -> np.ndarray:
    if samples < 16:
        raise ValueError("samples must be >=16")
    base = PeriodicCurve(points)
    dense_n = max(samples * dense_factor, len(points) * 4, 2048)
    q_dense = np.linspace(0.0, 1.0, dense_n, endpoint=False)
    p_dense = base.eval(q_dense)
    edges = np.roll(p_dense, -1, axis=0) - p_dense
    lengths = np.linalg.norm(edges, axis=1)
    cum = np.concatenate([[0.0], np.cumsum(lengths)])
    total = cum[-1]
    target = total * np.arange(samples) / samples
    q_ext = np.concatenate([q_dense, [1.0]])
    q_target = np.interp(target, cum, q_ext)
    return base.eval(q_target)


def polygon_length(points: np.ndarray) -> float:
    return float(np.linalg.norm(np.roll(points, -1, axis=0) - points, axis=1).sum())


def _periodic_derivative(values: np.ndarray, ds: float) -> np.ndarray:
    return (
        -np.roll(values, -2, axis=0)
        + 8.0 * np.roll(values, -1, axis=0)
        - 8.0 * np.roll(values, 1, axis=0)
        + np.roll(values, 2, axis=0)
    ) / (12.0 * ds)


def compute_geometry(points: np.ndarray) -> CurveGeometry:
    points = np.asarray(points, dtype=float)
    n = len(points)
    edges = np.roll(points, -1, axis=0) - points
    edge_lengths = np.linalg.norm(edges, axis=1)
    length = float(edge_lengths.sum())
    ds = length / n
    dp = _periodic_derivative(points, ds)
    tangents = dp / np.maximum(np.linalg.norm(dp, axis=1, keepdims=True), 1e-15)
    curvature_vectors = _periodic_derivative(tangents, ds)
    curvature = np.linalg.norm(curvature_vectors, axis=1)
    normals = np.zeros_like(points)
    good = curvature > 1e-12
    normals[good] = curvature_vectors[good] / curvature[good, None]
    binormals = np.cross(tangents, normals)
    bn = np.linalg.norm(binormals, axis=1, keepdims=True)
    binormals = np.divide(binormals, np.maximum(bn, 1e-15), out=np.zeros_like(binormals), where=bn > 0)
    db = _periodic_derivative(binormals, ds)
    torsion = -np.sum(db * normals, axis=1)
    return CurveGeometry(
        points=points,
        s=np.arange(n, dtype=float) / n,
        length=length,
        ds=ds,
        tangents=tangents,
        curvature_vectors=curvature_vectors,
        curvature=curvature,
        normals=normals,
        binormals=binormals,
        torsion=torsion,
        edge_lengths=edge_lengths,
        edge_ratio=float(edge_lengths.max() / edge_lengths.min()),
        edge_cv=float(edge_lengths.std() / edge_lengths.mean()),
    )


def sampled_thickness_proxy(geom: CurveGeometry, exclusion_fraction: float = 0.03) -> dict[str, float]:
    """Sampled min of local radius and double-critical half-distance proxy."""
    n = len(geom.points)
    exclusion = max(3, int(round(exclusion_fraction * n)))
    local_radius = np.divide(1.0, geom.curvature, out=np.full_like(geom.curvature, np.inf), where=geom.curvature > 1e-12)
    best = np.inf
    best_orth = np.inf
    for i in range(n):
        d = geom.points[i] - geom.points
        dist = np.linalg.norm(d, axis=1)
        idx = np.arange(n)
        cyc = np.minimum((idx - i) % n, (i - idx) % n)
        mask = cyc > exclusion
        if not np.any(mask):
            continue
        e = d[mask] / np.maximum(dist[mask, None], 1e-15)
        orth = np.sqrt((e @ geom.tangents[i]) ** 2 + np.sum(e * geom.tangents[mask], axis=1) ** 2)
        score = 0.5 * dist[mask] * (1.0 + 10.0 * orth * orth)
        jloc = int(np.argmin(score))
        candidate = 0.5 * dist[mask][jloc]
        if candidate < best:
            best = float(candidate)
            best_orth = float(orth[jloc])
    thickness = min(float(np.min(local_radius)), best)
    return {
        "thickness_proxy": thickness,
        "local_radius_min": float(np.min(local_radius)),
        "dcsd_half_proxy": best,
        "dcsd_orthogonality_at_min": best_orth,
        "ropelength_radius_proxy": geom.length / thickness,
        "ropelength_diameter_proxy": geom.length / (2.0 * thickness),
    }
