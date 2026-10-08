from __future__ import annotations
import numpy as np


def resample_closed(p: np.ndarray, n: int) -> np.ndarray:
    p = np.asarray(p, dtype=np.float64)
    q = np.vstack([p, p[0]])
    seg = np.linalg.norm(np.diff(q, axis=0), axis=1)
    s = np.r_[0.0, np.cumsum(seg)]
    L = float(s[-1])
    if not np.isfinite(L) or L <= 0:
        raise ValueError("degenerate centerline")
    target = np.linspace(0.0, L, int(n), endpoint=False)
    out = np.empty((int(n), 3), dtype=np.float64)
    for k, x in enumerate(target):
        i = min(np.searchsorted(s, x, side="right") - 1, len(p) - 1)
        u = (x - s[i]) / max(float(seg[i]), 1e-300)
        out[k] = (1.0 - u) * q[i] + u * q[i + 1]
    return out


def tangents(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, dtype=np.float64)
    d = np.roll(p, -1, axis=0) - np.roll(p, 1, axis=0)
    n = np.linalg.norm(d, axis=1)
    return d / np.maximum(n[:, None], 1e-300)


def polyline_stats(p: np.ndarray) -> dict:
    p = np.asarray(p, dtype=np.float64)
    d = np.roll(p, -1, axis=0) - p
    e = np.linalg.norm(d, axis=1)
    mean = float(np.mean(e))
    return {
        "n_vertices": int(len(p)),
        "length": float(np.sum(e)),
        "edge_mean": mean,
        "edge_min": float(np.min(e)),
        "edge_max": float(np.max(e)),
        "edge_cv": float(np.std(e) / max(mean, 1e-300)),
        "centroid": np.mean(p, axis=0).tolist(),
    }


def geom_stats(comps: list[np.ndarray]) -> tuple[list[dict], float]:
    rows = [polyline_stats(p) for p in comps]
    return rows, float(sum(r["length"] for r in rows))


def closure_edge_ratio(p: np.ndarray) -> float:
    p = np.asarray(p, dtype=np.float64)
    internal = np.linalg.norm(np.diff(p, axis=0), axis=1)
    gap = np.linalg.norm(p[-1] - p[0])
    return float(gap / max(float(np.median(internal)), 1e-300))


def curvature_radius_min(p: np.ndarray) -> float:
    p = np.asarray(p, dtype=np.float64)
    a = np.roll(p, 1, axis=0)
    b = p
    c = np.roll(p, -1, axis=0)
    ab = np.linalg.norm(b - a, axis=1)
    bc = np.linalg.norm(c - b, axis=1)
    ca = np.linalg.norm(a - c, axis=1)
    area2 = np.linalg.norm(np.cross(b - a, c - a), axis=1)
    R = ab * bc * ca / np.maximum(2.0 * area2, 1e-300)
    R = R[np.isfinite(R) & (R > 0)]
    return float(np.min(R)) if len(R) else float("inf")


def _segment_midpoints_tangents(p: np.ndarray):
    q = np.roll(p, -1, axis=0)
    dl = q - p
    m = 0.5 * (p + q)
    n = np.linalg.norm(dl, axis=1)
    t = dl / np.maximum(n[:, None], 1e-300)
    return m, t, dl


def doubly_critical_distance(a: np.ndarray, b: np.ndarray, same_component: bool, exclude_neighbors: int = 3, cos_tol: float = 0.20) -> float:
    ma, ta, _ = _segment_midpoints_tangents(np.asarray(a, float))
    mb, tb, _ = _segment_midpoints_tangents(np.asarray(b, float))
    r = mb[None, :, :] - ma[:, None, :]
    d = np.linalg.norm(r, axis=2)
    ca = np.abs(np.einsum("ijk,ik->ij", r, ta)) / np.maximum(d, 1e-300)
    cb = np.abs(np.einsum("ijk,jk->ij", r, tb)) / np.maximum(d, 1e-300)
    mask = (d > 1e-14) & (ca <= cos_tol) & (cb <= cos_tol)
    if same_component:
        n = len(ma)
        ii = np.arange(n)[:, None]
        jj = np.arange(n)[None, :]
        dij = np.abs(ii - jj)
        dij = np.minimum(dij, n - dij)
        mask &= dij > int(exclude_neighbors)
    vals = d[mask]
    return float(np.min(vals)) if vals.size else float("inf")


def min_midpoint_distance(a: np.ndarray, b: np.ndarray, same_component: bool, exclude_neighbors: int = 3) -> float:
    ma, _, _ = _segment_midpoints_tangents(np.asarray(a, float))
    mb, _, _ = _segment_midpoints_tangents(np.asarray(b, float))
    d = np.linalg.norm(mb[None, :, :] - ma[:, None, :], axis=2)
    mask = d > 1e-14
    if same_component:
        n = len(ma)
        ii = np.arange(n)[:, None]
        jj = np.arange(n)[None, :]
        dij = np.abs(ii - jj)
        dij = np.minimum(dij, n - dij)
        mask &= dij > int(exclude_neighbors)
    vals = d[mask]
    return float(np.min(vals)) if vals.size else float("inf")


def thickness_proxy(comps: list[np.ndarray]) -> dict:
    curv = min(curvature_radius_min(p) for p in comps)
    dcrit = float("inf")
    fallback = float("inf")
    for i, a in enumerate(comps):
        ex = max(3, int(round(0.05 * len(a))))
        dcrit = min(dcrit, doubly_critical_distance(a, a, True, ex, 0.22))
        fallback = min(fallback, min_midpoint_distance(a, a, True, max(ex, int(round(0.15 * len(a))))))
        for j in range(i + 1, len(comps)):
            dcrit = min(dcrit, doubly_critical_distance(a, comps[j], False, 0, 0.22))
            fallback = min(fallback, min_midpoint_distance(a, comps[j], False, 0))
    if not np.isfinite(dcrit):
        dcrit = fallback
    half = 0.5 * dcrit
    return {
        "curvature_radius_min": float(curv),
        "half_doubly_critical_distance_proxy": float(half),
        "fallback_half_nonlocal_distance": float(0.5 * fallback),
        "thickness_proxy": float(min(curv, half)),
    }


def vector_area(comps: list[np.ndarray]) -> np.ndarray:
    total = np.zeros(3, dtype=np.float64)
    for p in comps:
        q = np.roll(p, -1, axis=0)
        total += 0.5 * np.sum(np.cross(p, q), axis=0)
    return total


def bounding_radius(comps: list[np.ndarray]) -> tuple[np.ndarray, float]:
    pts = np.vstack(comps)
    c = np.mean(pts, axis=0)
    R = float(np.max(np.linalg.norm(pts - c, axis=1)))
    return c, R
