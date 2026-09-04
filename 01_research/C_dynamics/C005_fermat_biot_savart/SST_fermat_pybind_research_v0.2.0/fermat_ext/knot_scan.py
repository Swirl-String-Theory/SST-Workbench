from __future__ import annotations

import math
from typing import Any, Iterable

import numpy as np

from . import constants
from ._config import RESULT_SCHEMA
from .core import PACKAGE_VERSION, backend_biot_savart
from .knot_catalog import (
    DEFAULT_KNOT_IDS,
    centerline_summary,
    knot_metadata,
    sample_ideal_knot,
    validate_knot_ids,
)


def torus_knot(p: int, q: int, n: int, major_radius: float, minor_radius: float) -> np.ndarray:
    """Legacy generated torus-knot helper retained for comparison only."""
    if p <= 0 or q <= 0 or n < 16:
        raise ValueError("p,q>0 and n>=16 required")
    t = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    radial = major_radius + minor_radius * np.cos(q * t)
    return np.column_stack(
        (radial * np.cos(p * t), radial * np.sin(p * t), minor_radius * np.sin(q * t))
    )


def _unit(v: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(v))
    if norm <= 1e-15:
        raise ValueError("degenerate vector")
    return v / norm


def _rotate_rodrigues(v: np.ndarray, axis: np.ndarray, angle: float) -> np.ndarray:
    axis = _unit(axis)
    return (
        v * math.cos(angle)
        + np.cross(axis, v) * math.sin(angle)
        + axis * float(np.dot(axis, v)) * (1.0 - math.cos(angle))
    )


def parallel_transport_frames(curve: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Construct a discrete Bishop-like frame along a closed sampled centerline."""
    curve = np.asarray(curve, dtype=float)
    tangents = np.roll(curve, -1, axis=0) - np.roll(curve, 1, axis=0)
    tangents = tangents / np.linalg.norm(tangents, axis=1)[:, None]

    axes = np.eye(3)
    axis0 = axes[int(np.argmin(np.abs(axes @ tangents[0])))]
    n1 = np.empty_like(curve)
    n2 = np.empty_like(curve)
    n1[0] = _unit(np.cross(tangents[0], axis0))
    n2[0] = _unit(np.cross(tangents[0], n1[0]))

    for i in range(1, len(curve)):
        t0, t1 = tangents[i - 1], tangents[i]
        cross_t = np.cross(t0, t1)
        sin_angle = float(np.linalg.norm(cross_t))
        cos_angle = float(np.clip(np.dot(t0, t1), -1.0, 1.0))
        candidate = n1[i - 1]
        if sin_angle > 1e-14:
            candidate = _rotate_rodrigues(candidate, cross_t / sin_angle, math.atan2(sin_angle, cos_angle))
        elif cos_angle < 0.0:
            aux = axes[int(np.argmin(np.abs(axes @ t0)))]
            candidate = _rotate_rodrigues(candidate, np.cross(t0, aux), math.pi)
        candidate = candidate - float(np.dot(candidate, t1)) * t1
        n1[i] = _unit(candidate)
        n2[i] = _unit(np.cross(t1, n1[i]))

    # A diagnostic only: this is the residual frame mismatch after traversing
    # the discrete loop, not a physical twist assignment.
    closure_dot = float(np.clip(np.dot(n1[-1], n1[0]), -1.0, 1.0))
    frame_closure_mismatch = math.acos(closure_dot)
    return tangents, n1, n2, frame_closure_mismatch


def _quadratic_minimum(xs: np.ndarray, ys: np.ndarray, i: int) -> tuple[float, float]:
    if i <= 0 or i >= len(xs) - 1:
        return float(xs[i]), float(ys[i])
    coeff = np.polyfit(xs[i - 1 : i + 2], ys[i - 1 : i + 2], 2)
    if coeff[0] <= 0:
        return float(xs[i]), float(ys[i])
    x = float(-coeff[1] / (2 * coeff[0]))
    if not (xs[i - 1] <= x <= xs[i + 1]):
        return float(xs[i]), float(ys[i])
    return x, float(np.polyval(coeff, x))


def _scan_curve_raw(
    *,
    curve: np.ndarray,
    knot_info: dict[str, Any],
    stations: int,
    angles: int,
    rho_min: float,
    rho_max: float,
    radial_samples: int,
    epsilon: float,
    force_python: bool,
    auto_build: bool,
) -> tuple[dict[str, Any], np.ndarray]:
    if stations < 1 or angles < 3 or radial_samples < 5:
        raise ValueError("stations>=1, angles>=3, radial_samples>=5 required")
    if not (0.0 < rho_min < rho_max):
        raise ValueError("require 0<rho_min<rho_max")
    curve = np.asarray(curve, dtype=float)
    _, frame_n1, frame_n2, frame_mismatch = parallel_transport_frames(curve)
    station_indices = np.floor(np.arange(stations) * len(curve) / stations).astype(int)
    rhos = np.geomspace(rho_min, rho_max, radial_samples)

    descriptors: list[tuple[int, int, float, float]] = []
    probes: list[list[float]] = []
    for si, idx in enumerate(station_indices):
        n1, n2 = frame_n1[int(idx)], frame_n2[int(idx)]
        origin = curve[int(idx)]
        for ai in range(angles):
            theta = 2.0 * math.pi * ai / angles
            direction = math.cos(theta) * n1 + math.sin(theta) * n2
            for rho in rhos:
                probes.append((origin + rho * direction).tolist())
                descriptors.append((si, ai, float(theta), float(rho)))

    beta_vectors, backend = backend_biot_savart(
        curve.tolist(), probes, epsilon=epsilon,
        force_python=force_python, auto_build=auto_build,
    )
    beta_vectors_arr = np.asarray(beta_vectors, dtype=float)
    beta_mag = np.linalg.norm(beta_vectors_arr, axis=1)

    per_ray: dict[tuple[int, int], list[tuple[float, float, float]]] = {}
    invalid_clock = 0
    for desc, beta in zip(descriptors, beta_mag):
        si, ai, _, rho = desc
        if beta >= 1.0:
            invalid_clock += 1
            rf = math.nan
        else:
            rf = rho / math.sqrt(1.0 - beta * beta)
        per_ray.setdefault((si, ai), []).append((rho, rf, float(beta)))

    candidates: list[dict[str, Any]] = []
    for (si, ai), values in per_ray.items():
        arr = np.asarray(values, dtype=float)
        xs, ys, bs = arr[:, 0], arr[:, 1], arr[:, 2]
        finite = np.isfinite(ys)
        for i in range(1, len(xs) - 1):
            if finite[i - 1] and finite[i] and finite[i + 1] and ys[i] < ys[i - 1] and ys[i] < ys[i + 1]:
                x_min, y_min = _quadratic_minimum(xs, ys, i)
                candidates.append({
                    "station": int(si),
                    "centerline_index": int(station_indices[si]),
                    "angle_index": int(ai),
                    "theta_rad": 2.0 * math.pi * ai / angles,
                    "rho_over_rc": x_min,
                    "R_F_over_rc": y_min,
                    "nearest_sample_beta": float(bs[i]),
                    "classification": "LOCAL_TRANSVERSE_MINIMUM_CANDIDATE",
                })

    candidates.sort(key=lambda row: (row["station"], row["angle_index"], row["rho_over_rc"]))
    summary = centerline_summary(
        curve, knot_info.get("knot_id")
        if knot_info.get("centerline_source") == "uploaded_ideal_fourier_catalog" else None
    )
    result = {
        "schema": RESULT_SCHEMA,
        "package_version": PACKAGE_VERSION,
        "audit_name": "SST standalone local Fermat scan around an uploaded ideal-knot filament",
        "status": "RESEARCH_TRACK_DIAGNOSTIC_ONLY",
        "backend": backend,
        "canonical_constants": constants.as_dict(),
        "knot": knot_info,
        "centerline": summary,
        "input": {
            "centerline_points": int(len(curve)),
            "stations": stations,
            "angles": angles,
            "rho_min_over_rc": rho_min,
            "rho_max_over_rc": rho_max,
            "radial_samples": radial_samples,
            "biot_savart_softening_over_rc": epsilon,
        },
        "frame_transport": {
            "method": "discrete_Bishop_parallel_transport",
            "closure_mismatch_rad": frame_mismatch,
            "physical_twist_certified": False,
        },
        "field_summary": {
            "beta_min": float(beta_mag.min()) if len(beta_mag) else None,
            "beta_max": float(beta_mag.max()) if len(beta_mag) else None,
            "beta_mean": float(beta_mag.mean()) if len(beta_mag) else None,
            "beta_rms": float(math.sqrt(float(np.mean(beta_mag * beta_mag)))) if len(beta_mag) else None,
            "vector_component_sums": beta_vectors_arr.sum(axis=0).tolist() if len(beta_mag) else [0.0, 0.0, 0.0],
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
    return result, beta_vectors_arr


def scan_catalog_knot(
    *,
    knot_id: str,
    centerline_points: int = 512,
    scale_over_rc: float = 1.0,
    stations: int = 16,
    angles: int = 24,
    rho_min: float = 0.002,
    rho_max: float = 0.05,
    radial_samples: int = 160,
    epsilon: float = 0.0045,
    force_python: bool = False,
    auto_build: bool = True,
) -> dict[str, Any]:
    curve = sample_ideal_knot(knot_id, centerline_points, scale_over_rc=scale_over_rc)
    info = knot_metadata(knot_id)
    info.update({
        "centerline_source": "uploaded_ideal_fourier_catalog",
        "scale_over_rc": scale_over_rc,
        "uniform_arclength_resampled": True,
    })
    result, _ = _scan_curve_raw(
        curve=curve, knot_info=info, stations=stations, angles=angles,
        rho_min=rho_min, rho_max=rho_max, radial_samples=radial_samples,
        epsilon=epsilon, force_python=force_python, auto_build=auto_build,
    )
    return result


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
    result, _ = _scan_curve_raw(
        curve=curve,
        knot_info={
            "knot_id": f"T({p},{q})",
            "centerline_source": "generated_torus_parametrization",
            "p": p,
            "q": q,
            "major_radius_over_rc": major_radius,
            "minor_radius_over_rc": minor_radius,
        },
        stations=stations, angles=angles, rho_min=rho_min, rho_max=rho_max,
        radial_samples=radial_samples, epsilon=epsilon,
        force_python=force_python, auto_build=auto_build,
    )
    return result


def _candidate_rho_parity(primary: dict[str, Any], python: dict[str, Any]) -> float | None:
    a = primary["candidates"]
    b = python["candidates"]
    if len(a) != len(b):
        return None
    if not a:
        return 0.0
    diffs: list[float] = []
    for ca, cb in zip(a, b):
        key_a = (ca["station"], ca["angle_index"])
        key_b = (cb["station"], cb["angle_index"])
        if key_a != key_b:
            return None
        diffs.append(abs(float(ca["rho_over_rc"]) - float(cb["rho_over_rc"])))
    return max(diffs)


def scan_catalog_matrix(
    knot_ids: Iterable[str] = DEFAULT_KNOT_IDS,
    *,
    centerline_points: int = 256,
    scale_over_rc: float = 1.0,
    stations: int = 8,
    angles: int = 12,
    rho_min: float = 0.002,
    rho_max: float = 0.05,
    radial_samples: int = 80,
    epsilon: float = 0.0045,
    auto_build: bool = True,
    force_build_first: bool = False,
) -> dict[str, Any]:
    ids = validate_knot_ids(knot_ids)
    rows: list[dict[str, Any]] = []
    results: dict[str, dict[str, Any]] = {}

    for index, knot_id in enumerate(ids):
        curve = sample_ideal_knot(knot_id, centerline_points, scale_over_rc=scale_over_rc)
        info = knot_metadata(knot_id)
        info.update({
            "centerline_source": "uploaded_ideal_fourier_catalog",
            "scale_over_rc": scale_over_rc,
            "uniform_arclength_resampled": True,
        })
        py_result, py_beta = _scan_curve_raw(
            curve=curve, knot_info=info, stations=stations, angles=angles,
            rho_min=rho_min, rho_max=rho_max, radial_samples=radial_samples,
            epsilon=epsilon, force_python=True, auto_build=False,
        )
        primary_result, primary_beta = _scan_curve_raw(
            curve=curve, knot_info=info, stations=stations, angles=angles,
            rho_min=rho_min, rho_max=rho_max, radial_samples=radial_samples,
            epsilon=epsilon, force_python=False,
            auto_build=auto_build if index == 0 else False,
        )
        vector_linf = float(np.max(np.abs(primary_beta - py_beta)))
        magnitude_linf = float(
            np.max(
                np.abs(
                    np.linalg.norm(primary_beta, axis=1) - np.linalg.norm(py_beta, axis=1)
                )
            )
        )
        candidate_rho_error = _candidate_rho_parity(primary_result, py_result)
        native = primary_result["backend"]["backend"] == "cpp"
        parity_ok = (
            native
            and vector_linf < 1e-10
            and magnitude_linf < 1e-10
            and primary_result["candidate_count"] == py_result["candidate_count"]
            and primary_result["invalid_clock_probe_count"] == py_result["invalid_clock_probe_count"]
            and candidate_rho_error is not None
            and candidate_rho_error < 1e-10
        )
        row = {
            "knot_id": knot_id,
            "source_id": info["source_id"],
            "source_length_L": info["source_length_L"],
            "coefficient_count": info["coefficient_count"],
            "primary_backend": primary_result["backend"]["backend"],
            "native_available": native,
            "probe_count": primary_result["probe_count"],
            "candidate_count_primary": primary_result["candidate_count"],
            "candidate_count_python": py_result["candidate_count"],
            "invalid_clock_primary": primary_result["invalid_clock_probe_count"],
            "invalid_clock_python": py_result["invalid_clock_probe_count"],
            "beta_vector_linf_error": vector_linf,
            "beta_magnitude_linf_error": magnitude_linf,
            "candidate_rho_linf_error": candidate_rho_error,
            "source_length_relative_error": primary_result["centerline"]["source_length_relative_error"],
            "native_python_parity_ok": parity_ok,
            "global_closed_orbit_certified": False,
            "qsm_certified": False,
        }
        rows.append(row)
        results[knot_id] = {"primary": primary_result, "python": py_result, "parity": row}

    native_all = all(row["native_available"] for row in rows)
    parity_all = native_all and all(row["native_python_parity_ok"] for row in rows)
    return {
        "schema": "sst.fermat.knot-matrix.v0.2",
        "package_version": PACKAGE_VERSION,
        "status": "RESEARCH_TRACK_DIAGNOSTIC_ONLY",
        "knot_ids": list(ids),
        "settings": {
            "centerline_points": centerline_points,
            "scale_over_rc": scale_over_rc,
            "stations": stations,
            "angles": angles,
            "rho_min_over_rc": rho_min,
            "rho_max_over_rc": rho_max,
            "radial_samples": radial_samples,
            "biot_savart_softening_over_rc": epsilon,
        },
        "rows": rows,
        "results": results,
        "native_available_for_all_knots": native_all,
        "native_python_parity_certified_for_all_knots": parity_all,
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }
