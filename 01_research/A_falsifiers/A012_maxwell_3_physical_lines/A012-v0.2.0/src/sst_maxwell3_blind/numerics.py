from __future__ import annotations
import hashlib
import math
from typing import Iterable
import numpy as np


def periodic_box_filter(a: np.ndarray, radius: int) -> np.ndarray:
    """Separable periodic box filter. Last axes may contain vector/tensor components."""
    out = np.asarray(a, dtype=float)
    if radius <= 0:
        return out.copy()
    spatial_axes = tuple(range(out.ndim - (1 if out.shape[-1] in (2, 3, 6, 9) else 0)))
    # The package uses this only for scalar or (...,3) arrays. Limit to first 3 axes.
    spatial_axes = spatial_axes[:3]
    for axis in spatial_axes:
        acc = np.zeros_like(out, dtype=float)
        for k in range(-radius, radius + 1):
            acc += np.roll(out, k, axis=axis)
        out = acc / float(2 * radius + 1)
    return out


def central_diff_periodic(a: np.ndarray, spacing: float, axis: int) -> np.ndarray:
    return (np.roll(a, -1, axis=axis) - np.roll(a, 1, axis=axis)) / (2.0 * spacing)


def curl_periodic(u: np.ndarray, spacing: Iterable[float]) -> np.ndarray:
    dx, dy, dz = [float(x) for x in spacing]
    ux, uy, uz = u[..., 0], u[..., 1], u[..., 2]
    wx = central_diff_periodic(uz, dy, 1) - central_diff_periodic(uy, dz, 2)
    wy = central_diff_periodic(ux, dz, 2) - central_diff_periodic(uz, dx, 0)
    wz = central_diff_periodic(uy, dx, 0) - central_diff_periodic(ux, dy, 1)
    return np.stack((wx, wy, wz), axis=-1)


def deterministic_fraction(key: str, seed: str) -> float:
    h = hashlib.sha256((seed + "|" + key).encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big") / float(2**64 - 1)


def scalar_fit_through_origin(x: np.ndarray, y: np.ndarray) -> float:
    num = float(np.sum(x * y))
    den = float(np.sum(x * x))
    return num / den if den > 0 else float("nan")


def nrmse(y: np.ndarray, yhat: np.ndarray) -> float:
    den = float(np.sqrt(np.mean(np.sum(np.asarray(y) ** 2, axis=-1))))
    num = float(np.sqrt(np.mean(np.sum((np.asarray(y) - np.asarray(yhat)) ** 2, axis=-1))))
    return num / den if den > 0 else float("inf")


def cosine_median(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, float); y = np.asarray(y, float)
    xn = np.linalg.norm(x, axis=-1); yn = np.linalg.norm(y, axis=-1)
    good = (xn > 0) & (yn > 0)
    if not np.any(good):
        return float("nan")
    c = np.abs(np.sum(x[good] * y[good], axis=-1) / (xn[good] * yn[good]))
    return float(np.median(np.clip(c, 0.0, 1.0)))


def coefficient_of_variation(values: list[float]) -> float:
    a = np.asarray([v for v in values if np.isfinite(v)], float)
    if a.size < 2:
        return float("nan")
    m = float(np.mean(np.abs(a)))
    return float(np.std(a, ddof=1) / m) if m > 0 else float("inf")


def r2_score(y: np.ndarray, yhat: np.ndarray) -> float:
    y = np.asarray(y, float).ravel(); yhat = np.asarray(yhat, float).ravel()
    ss_res = float(np.sum((y - yhat)**2))
    ss_tot = float(np.sum((y - np.mean(y))**2))
    return 1.0 - ss_res/ss_tot if ss_tot > 0 else (1.0 if ss_res == 0 else float("-inf"))
