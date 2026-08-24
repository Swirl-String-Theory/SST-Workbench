from __future__ import annotations
import math
import numpy as np


def clean_curve(points: np.ndarray) -> np.ndarray:
    p = np.asarray(points, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3:
        raise ValueError("curve must be Nx3")
    if len(p) < 8 or not np.isfinite(p).all():
        raise ValueError("curve must contain >=8 finite points")
    # Remove consecutive duplicates.
    d = np.linalg.norm(np.diff(p, axis=0), axis=1)
    geom_scale = max(float(np.linalg.norm(np.ptp(p, axis=0))), float(np.max(np.abs(p))), 1e-300)
    keep = np.r_[True, d > 1e-12 * geom_scale]
    p = p[keep]
    if len(p) >= 2 and np.linalg.norm(p[0] - p[-1]) <= 1e-10 * geom_scale:
        p = p[:-1]
    if len(p) < 8:
        raise ValueError("too few unique points")
    return np.ascontiguousarray(p, dtype=float)


def curve_length(p: np.ndarray) -> float:
    q = np.roll(p, -1, axis=0)
    return float(np.linalg.norm(q - p, axis=1).sum())


def radius_of_gyration(p: np.ndarray) -> float:
    c = np.mean(p, axis=0)
    return float(np.sqrt(np.mean(np.sum((p - c) ** 2, axis=1))))


def resample_closed(p: np.ndarray, n: int) -> np.ndarray:
    p = clean_curve(p)
    n = int(n)
    if n < 16:
        raise ValueError("resample n must be >=16")
    q = np.vstack([p, p[0]])
    seg = np.linalg.norm(np.diff(q, axis=0), axis=1)
    if np.any(seg <= 0):
        raise ValueError("zero-length segment")
    s = np.r_[0.0, np.cumsum(seg)]
    target = np.linspace(0.0, s[-1], n, endpoint=False)
    out = np.empty((n, 3), float)
    for k in range(3):
        out[:, k] = np.interp(target, s, q[:, k])
    return np.ascontiguousarray(out)


def nonadjacent_point_distance(p: np.ndarray, exclude_fraction: float = 0.03) -> float:
    n = len(p)
    skip = max(3, int(math.ceil(float(exclude_fraction) * n)))
    best = float("inf")
    # O(N^2), used only in preflight/physicalization.
    for i in range(n):
        d = np.linalg.norm(p[i+1:] - p[i], axis=1)
        for off, value in enumerate(d, start=1):
            cyc = min(off, n - off)
            if cyc > skip and value < best:
                best = float(value)
    return best


def physicalize_thickness_to_rc(p: np.ndarray, r_c: float, exclude_fraction: float = 0.03) -> tuple[np.ndarray, dict]:
    p = clean_curve(p)
    c = np.mean(p, axis=0)
    centered = p - c
    dmin = nonadjacent_point_distance(centered, exclude_fraction)
    if not np.isfinite(dmin) or dmin <= 0:
        raise ValueError("cannot estimate nonadjacent thickness proxy")
    tube_radius_proxy = 0.5 * dmin
    scale = float(r_c) / tube_radius_proxy
    phys = centered * scale
    return np.ascontiguousarray(phys), {
        "scale_factor_m_per_input_unit": scale,
        "input_nonadjacent_min": dmin,
        "tube_radius_proxy_input": tube_radius_proxy,
        "physical_nonadjacent_min_m": dmin * scale,
        "physical_rg_m": radius_of_gyration(phys),
        "physical_length_m": curve_length(phys),
    }


def pca_frame(p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    c = np.mean(p, axis=0)
    x = p - c
    cov = (x.T @ x) / len(x)
    vals, vecs = np.linalg.eigh(cov)
    order = np.argsort(vals)[::-1]
    R = vecs[:, order]
    if np.linalg.det(R) < 0:
        R[:, -1] *= -1
    return c, R


def affine_constriction(p: np.ndarray, eta: float) -> np.ndarray:
    """Volume-preserving affine squeeze det(S)=1 in the PCA frame."""
    c, R = pca_frame(p)
    local = (p - c) @ R
    s = np.diag([math.exp(-eta), math.exp(-eta), math.exp(2.0 * eta)])
    return np.ascontiguousarray((local @ s) @ R.T + c)


def perturb_curve(p: np.ndarray, mode: int, amplitude_m: float, kind: str = "normal") -> np.ndarray:
    """Deterministic smooth centerline perturbation, topology-preserving for small amplitude."""
    n = len(p)
    prev = np.roll(p, 1, axis=0)
    nxt = np.roll(p, -1, axis=0)
    tang = nxt - prev
    tang /= np.maximum(np.linalg.norm(tang, axis=1)[:, None], 1e-300)
    curv = nxt - 2.0 * p + prev
    # Remove tangential component from curvature vector.
    curv -= np.sum(curv * tang, axis=1)[:, None] * tang
    cn = np.linalg.norm(curv, axis=1)
    normal = np.zeros_like(p)
    good = cn > 1e-14 * max(radius_of_gyration(p), 1e-300)
    normal[good] = curv[good] / cn[good, None]
    if not np.all(good):
        # PCA direction projected normal to tangent as deterministic fallback.
        _, R = pca_frame(p)
        ref = np.broadcast_to(R[:, 1], p.shape).copy()
        ref -= np.sum(ref * tang, axis=1)[:, None] * tang
        ref /= np.maximum(np.linalg.norm(ref, axis=1)[:, None], 1e-300)
        normal[~good] = ref[~good]
    binormal = np.cross(tang, normal)
    binormal /= np.maximum(np.linalg.norm(binormal, axis=1)[:, None], 1e-300)
    direction = normal if kind == "normal" else binormal
    phase = 2.0 * np.pi * int(mode) * np.arange(n) / n
    disp = float(amplitude_m) * np.sin(phase)[:, None] * direction
    disp -= np.mean(disp, axis=0)
    return np.ascontiguousarray(p + disp)


def kabsch_align(moving: np.ndarray, reference: np.ndarray) -> np.ndarray:
    a = np.asarray(moving, float)
    b = np.asarray(reference, float)
    ca, cb = a.mean(axis=0), b.mean(axis=0)
    A, B = a - ca, b - cb
    H = A.T @ B
    U, _, Vt = np.linalg.svd(H)
    R = U @ Vt
    if np.linalg.det(R) < 0:
        U[:, -1] *= -1
        R = U @ Vt
    return (A @ R) + cb


def impulse(p: np.ndarray, rho: float, gamma: float) -> np.ndarray:
    q = np.roll(p, -1, axis=0)
    return 0.5 * float(rho) * float(gamma) * np.sum(np.cross(p, q), axis=0)
