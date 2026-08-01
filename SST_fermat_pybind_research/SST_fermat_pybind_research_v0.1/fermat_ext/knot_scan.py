from __future__ import annotations

import math
from typing import Any

import numpy as np

from . import constants
from ._config import RESULT_SCHEMA
from .core import PACKAGE_VERSION, backend_biot_savart


def torus_knot(p: int, q: int, n: int, major_radius: float, minor_radius: float) -> np.ndarray:
    if p <= 0 or q <= 0 or n < 16:
        raise ValueError("p,q>0 and n>=16 required")
    t = np.linspace(0.0, 2.0*math.pi, n, endpoint=False)
    radial = major_radius + minor_radius*np.cos(q*t)
    return np.column_stack((radial*np.cos(p*t), radial*np.sin(p*t), minor_radius*np.sin(q*t)))


def _unit(v: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(v))
    if norm <= 1e-15:
        raise ValueError("degenerate vector")
    return v/norm


def local_frame(curve: np.ndarray, i: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    t = _unit(curve[(i+1) % len(curve)] - curve[(i-1) % len(curve)])
    axes = np.eye(3)
    axis = axes[int(np.argmin(np.abs(axes @ t)))]
    n1 = _unit(np.cross(t, axis))
    n2 = _unit(np.cross(t, n1))
    return t, n1, n2


def _quadratic_minimum(xs: np.ndarray, ys: np.ndarray, i: int) -> tuple[float, float]:
    if i <= 0 or i >= len(xs)-1:
        return float(xs[i]), float(ys[i])
    coeff = np.polyfit(xs[i-1:i+2], ys[i-1:i+2], 2)
    if coeff[0] <= 0:
        return float(xs[i]), float(ys[i])
    x = float(-coeff[1]/(2*coeff[0]))
    if not (xs[i-1] <= x <= xs[i+1]):
        return float(xs[i]), float(ys[i])
    return x, float(np.polyval(coeff, x))


def scan_torus_knot(
    *,
    p: int = 2,
    q: int = 3,
    centerline_points: int = 240,
    major_radius: float = 1.0,
    minor_radius: float = 0.35,
    stations: int = 12,
    angles: int = 16,
    rho_min: float = 0.002,
    rho_max: float = 0.05,
    radial_samples: int = 120,
    epsilon: float = 0.0045,
    force_python: bool = False,
    auto_build: bool = True,
) -> dict[str, Any]:
    curve = torus_knot(p, q, centerline_points, major_radius, minor_radius)
    station_indices = np.linspace(0, centerline_points, stations, endpoint=False, dtype=int)
    rhos = np.geomspace(rho_min, rho_max, radial_samples)
    descriptors: list[tuple[int, int, float, float]] = []
    probes: list[list[float]] = []
    for si, idx in enumerate(station_indices):
        _, n1, n2 = local_frame(curve, int(idx))
        origin = curve[int(idx)]
        for ai in range(angles):
            theta = 2*math.pi*ai/angles
            direction = math.cos(theta)*n1 + math.sin(theta)*n2
            for rho in rhos:
                probes.append((origin + rho*direction).tolist())
                descriptors.append((si, ai, float(theta), float(rho)))

    beta_vectors, backend = backend_biot_savart(
        curve.tolist(), probes, epsilon=epsilon,
        force_python=force_python, auto_build=auto_build,
    )
    beta_mag = np.linalg.norm(np.asarray(beta_vectors), axis=1)
    per_ray: dict[tuple[int, int], list[tuple[float, float]]] = {}
    invalid_clock = 0
    for desc, beta in zip(descriptors, beta_mag):
        si, ai, _, rho = desc
        if beta >= 1.0:
            invalid_clock += 1
            rf = math.nan
        else:
            rf = rho/math.sqrt(1.0-beta*beta)
        per_ray.setdefault((si, ai), []).append((rho, rf))

    candidates: list[dict[str, Any]] = []
    for (si, ai), values in per_ray.items():
        arr = np.asarray(values, dtype=float)
        xs, ys = arr[:, 0], arr[:, 1]
        finite = np.isfinite(ys)
        for i in range(1, len(xs)-1):
            if finite[i-1] and finite[i] and finite[i+1] and ys[i] < ys[i-1] and ys[i] < ys[i+1]:
                x_min, y_min = _quadratic_minimum(xs, ys, i)
                candidates.append({
                    "station": int(si),
                    "centerline_index": int(station_indices[si]),
                    "angle_index": int(ai),
                    "theta_rad": 2*math.pi*ai/angles,
                    "rho_over_rc": x_min,
                    "R_F_over_rc": y_min,
                    "classification": "LOCAL_TRANSVERSE_MINIMUM_CANDIDATE",
                })

    return {
        "schema": RESULT_SCHEMA,
        "package_version": PACKAGE_VERSION,
        "audit_name": "SST standalone local Fermat scan around a torus-knot filament",
        "status": "RESEARCH_TRACK_DIAGNOSTIC_ONLY",
        "backend": backend,
        "canonical_constants": constants.as_dict(),
        "input": {
            "p": p, "q": q, "centerline_points": centerline_points,
            "major_radius_over_rc": major_radius,
            "minor_radius_over_rc": minor_radius,
            "stations": stations, "angles": angles,
            "rho_min_over_rc": rho_min, "rho_max_over_rc": rho_max,
            "radial_samples": radial_samples,
            "biot_savart_softening_over_rc": epsilon,
        },
        "candidate_count": len(candidates),
        "candidates": candidates,
        "invalid_clock_probe_count": invalid_clock,
        "probe_count": len(probes),
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
        "guard": (
            "Local minima of rho/S in selected normal planes are not equivalent to "
            "closed Fermat geodesics in the full non-axisymmetric metric."
        ),
    }
