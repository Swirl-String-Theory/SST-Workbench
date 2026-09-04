#!/usr/bin/env python3
"""Gilbert ideal-knot usability: thickness-partition contact score C_cont.

A true ideal knot is self-contacting. Many Fourier AB records in Brian Gilbert's
database reconstruct with no self-contact and kappa_hat_max = 2 exactly
(curvature-only artifacts). Reject those before treating a record as ideal:

    C_cont > 0.05

Operational score (D = tube diameter from metadata):
    Exclude an arc ~pi*(D/2) when measuring non-adjacent centerline distance d_min.
    C_cont = clamp( (2D - d_min) / D, 0, 1 )

So tight contact (d_min ~= D) -> C_cont ~= 1, while a round circle of radius R=D
(d_min ~= 2D) -> C_cont ~= 0. kappa_hat_max is reported alongside for diagnostics.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

DEFAULT_MIN_C_CONT = 0.05
DEFAULT_SAMPLES = 384
_EPS = 1e-15

CoeffList = Sequence[
    tuple[int, tuple[float, float, float], tuple[float, float, float]]
]


def _as_closed_array(
    points: Sequence[Sequence[float]] | np.ndarray,
) -> np.ndarray:
    arr = np.asarray(points, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise ValueError("points must have shape (N, 3)")
    if arr.shape[0] < 8:
        raise ValueError("need at least 8 sample points")
    return arr


def edge_lengths(points: np.ndarray) -> np.ndarray:
    nxt = np.roll(points, -1, axis=0)
    return np.linalg.norm(nxt - points, axis=1)


def polygonal_length(points: np.ndarray) -> float:
    return float(np.sum(edge_lengths(points)))


def discrete_curvature(
    points: Sequence[Sequence[float]] | np.ndarray,
) -> np.ndarray:
    pts = _as_closed_array(points)
    prev = np.roll(pts, 1, axis=0)
    nxt = np.roll(pts, -1, axis=0)
    e1 = pts - prev
    e2 = nxt - pts
    len1 = np.linalg.norm(e1, axis=1)
    len2 = np.linalg.norm(e2, axis=1)
    t1 = e1 / np.maximum(len1[:, None], _EPS)
    t2 = e2 / np.maximum(len2[:, None], _EPS)
    dots = np.clip(np.sum(t1 * t2, axis=1), -1.0, 1.0)
    turn = np.arccos(dots)
    ds = 0.5 * (len1 + len2)
    return turn / np.maximum(ds, _EPS)


def fourier_sample_with_kappa(
    coeffs: CoeffList, n: int
) -> tuple[np.ndarray, np.ndarray]:
    if n < 8:
        raise ValueError("need at least 8 sample points")
    t = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    r = np.zeros((n, 3), dtype=float)
    rp = np.zeros((n, 3), dtype=float)
    rpp = np.zeros((n, 3), dtype=float)
    for idx, avec, bvec in coeffs:
        a = np.asarray(avec, dtype=float)
        b = np.asarray(bvec, dtype=float)
        if idx == 0:
            r += a
            continue
        k = float(idx)
        ct = np.cos(k * t)
        st = np.sin(k * t)
        r += ct[:, None] * a[None, :] + st[:, None] * b[None, :]
        rp += (-k * st)[:, None] * a[None, :] + (k * ct)[:, None] * b[None, :]
        rpp += (
            (-(k * k) * ct)[:, None] * a[None, :]
            + (-(k * k) * st)[:, None] * b[None, :]
        )
    cross = np.cross(rp, rpp)
    num = np.linalg.norm(cross, axis=1)
    speed = np.linalg.norm(rp, axis=1)
    kappa = num / np.maximum(speed ** 3, _EPS)
    return r, kappa


def kappa_hat_max(
    points: Sequence[Sequence[float]] | np.ndarray,
    D: float = 1.0,
    *,
    kappa: np.ndarray | None = None,
) -> float:
    if kappa is None:
        kappa = discrete_curvature(points)
    return float(D) * float(np.max(kappa))


def closed_min_distance(
    points: Sequence[Sequence[float]] | np.ndarray,
    local_skip: int | None = None,
) -> float:
    pts = _as_closed_array(points)
    n = pts.shape[0]
    if local_skip is None:
        local_skip = max(3, n // 16)
    local_skip = int(min(max(local_skip, 2), n // 2 - 1))
    dmin = float("inf")
    for i in range(n):
        for j in range(i + 1, n):
            cyclic = min(j - i, n - (j - i))
            if cyclic < local_skip:
                continue
            d = float(np.linalg.norm(pts[i] - pts[j]))
            if d < dmin:
                dmin = d
    if not math.isfinite(dmin):
        raise ValueError("failed to compute closed min distance")
    return dmin


def _adaptive_local_skip(
    points: np.ndarray,
    D: float,
    *,
    kappa_max: float | None = None,
) -> int:
    """Exclude ~π·R along the curve; R = max(D/2, 1/κ_max) when κ known."""
    n = points.shape[0]
    lengths = edge_lengths(points)
    mean_edge = float(np.mean(lengths))
    if mean_edge <= _EPS:
        return max(3, n // 16)
    a = 0.5 * float(D)
    if kappa_max is not None and kappa_max > _EPS:
        r_excl = max(a, 1.0 / float(kappa_max))
    else:
        r_excl = a
    exclude_arc = math.pi * r_excl
    skip = int(math.ceil(exclude_arc / mean_edge))
    return int(min(max(skip, 3), n // 2 - 1))


def i_kappa2(
    points: Sequence[Sequence[float]] | np.ndarray,
    D: float = 1.0,
    *,
    kappa: np.ndarray | None = None,
) -> float:
    pts = _as_closed_array(points)
    if kappa is None:
        kappa = discrete_curvature(pts)
    ds = edge_lengths(pts)
    return float(D) * float(np.sum((np.asarray(kappa, dtype=float) ** 2) * ds))


def c_cont(
    points: Sequence[Sequence[float]] | np.ndarray,
    D: float = 1.0,
    *,
    local_skip: int | None = None,
    kappa: np.ndarray | None = None,
) -> float:
    """Contact occupancy in [0, 1] from centerline self-distance vs D."""
    pts = _as_closed_array(points)
    if D <= 0:
        raise ValueError("D must be positive")
    kappa_max = None
    if kappa is not None:
        kappa_max = float(np.max(np.asarray(kappa, dtype=float)))
    skip = (
        local_skip
        if local_skip is not None
        else _adaptive_local_skip(pts, D, kappa_max=kappa_max)
    )
    d_min = closed_min_distance(pts, local_skip=skip)
    score = (2.0 * float(D) - d_min) / float(D)
    return float(min(1.0, max(0.0, score)))


def is_usable_ideal(
    points: Sequence[Sequence[float]] | np.ndarray,
    D: float = 1.0,
    *,
    min_c_cont: float = DEFAULT_MIN_C_CONT,
    local_skip: int | None = None,
    kappa: np.ndarray | None = None,
) -> bool:
    return c_cont(points, D, local_skip=local_skip, kappa=kappa) > min_c_cont


def usability_report(
    points: Sequence[Sequence[float]] | np.ndarray,
    D: float = 1.0,
    *,
    min_c_cont: float = DEFAULT_MIN_C_CONT,
    local_skip: int | None = None,
    kappa: np.ndarray | None = None,
) -> dict[str, float | bool]:
    pts = _as_closed_array(points)
    if kappa is None:
        kappa = discrete_curvature(pts)
    score = c_cont(pts, D, local_skip=local_skip, kappa=kappa)
    length = polygonal_length(pts)
    return {
        "C_cont": score,
        "kappa_hat_max": kappa_hat_max(pts, D, kappa=kappa),
        "L": length,
        "L_D": length / float(D) if D else float("nan"),
        "I_kappa2": i_kappa2(pts, D, kappa=kappa),
        "usable": score > min_c_cont,
        "min_c_cont": float(min_c_cont),
        "D": float(D),
    }


def usability_from_coeffs(
    coeffs: CoeffList,
    D: float = 1.0,
    *,
    samples: int = DEFAULT_SAMPLES,
    min_c_cont: float = DEFAULT_MIN_C_CONT,
    local_skip: int | None = None,
) -> tuple[np.ndarray, dict[str, float | bool]]:
    pts, kappa = fourier_sample_with_kappa(coeffs, samples)
    return pts, usability_report(
        pts, D, min_c_cont=min_c_cont, local_skip=local_skip, kappa=kappa
    )


class CurvatureOnlyIdealError(ValueError):
    """Raised when a Gilbert record fails the C_cont usability gate."""


def require_usable_ideal(
    points: Sequence[Sequence[float]] | np.ndarray,
    D: float = 1.0,
    *,
    min_c_cont: float = DEFAULT_MIN_C_CONT,
    knot_id: str | None = None,
    allow_curvature_only: bool = False,
    local_skip: int | None = None,
    kappa: np.ndarray | None = None,
) -> dict[str, float | bool]:
    report = usability_report(
        points,
        D,
        min_c_cont=min_c_cont,
        local_skip=local_skip,
        kappa=kappa,
    )
    if allow_curvature_only or report["usable"]:
        return report
    label = knot_id or "record"
    raise CurvatureOnlyIdealError(
        f"Gilbert {label} fails C_cont gate: "
        f"C_cont={report['C_cont']:.6g} <= {min_c_cont} "
        f"(kappa_hat_max={report['kappa_hat_max']:.6g}). "
        f"Likely a curvature-only Fourier artifact; "
        f"pass allow_curvature_only=True only for diagnostics."
    )
