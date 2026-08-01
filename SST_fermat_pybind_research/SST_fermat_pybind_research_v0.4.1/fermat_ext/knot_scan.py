from __future__ import annotations

import math
from typing import Any, Iterable, Sequence

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
from .resolution import resolution_plan

KERNEL_MODELS = ("rosenhead_midpoint",)


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
    tangent_norms = np.linalg.norm(tangents, axis=1)
    if np.any(tangent_norms <= 1e-15):
        raise ValueError("degenerate centerline tangent")
    tangents = tangents / tangent_norms[:, None]

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


def rosenhead_reference_regime(epsilon: float) -> dict[str, Any]:
    if epsilon <= 0.0:
        raise ValueError("epsilon must be positive")
    horizon_threshold = constants.ROSENHEAD_HORIZON_THRESHOLD
    critical_threshold = constants.ROSENHEAD_CRITICAL_THRESHOLD
    beta_max = constants.BETA_0 / (2.0 * epsilon)
    if epsilon <= horizon_threshold:
        classification = "STRAIGHT_REFERENCE_CLOCK_DEGENERACY_POSSIBLE"
    elif epsilon <= critical_threshold:
        classification = "STRAIGHT_REFERENCE_HORIZON_FREE_CRITICAL_WINDOW"
    else:
        classification = "STRAIGHT_REFERENCE_NO_FERMAT_CRITICAL_RADIUS"
    return {
        "kernel_model": "rosenhead_midpoint",
        "epsilon_over_rc": epsilon,
        "straight_reference_beta_max": beta_max,
        "horizon_threshold_epsilon_over_rc": horizon_threshold,
        "critical_threshold_epsilon_over_rc": critical_threshold,
        "epsilon_over_critical_threshold": epsilon / critical_threshold,
        "classification": classification,
        "scope_guard": (
            "This threshold is exact for the infinite straight Rosenhead reference profile; "
            "curvature and non-local knot contributions can shift the full-knot result."
        ),
    }


def _build_probe_geometry(
    curve: np.ndarray,
    *,
    stations: int,
    angles: int,
    rho_min: float,
    rho_max: float,
    radial_samples: int,
) -> dict[str, Any]:
    if stations < 1 or angles < 3 or radial_samples < 5:
        raise ValueError("stations>=1, angles>=3, radial_samples>=5 required")
    if not (0.0 < rho_min < rho_max):
        raise ValueError("require 0<rho_min<rho_max")
    curve = np.asarray(curve, dtype=float)
    _, frame_n1, frame_n2, frame_mismatch = parallel_transport_frames(curve)
    station_indices = np.floor(np.arange(stations) * len(curve) / stations).astype(int)
    rhos = np.geomspace(rho_min, rho_max, radial_samples)

    descriptors: list[tuple[int, int, float, float]] = []
    probes: list[np.ndarray] = []
    for si, idx in enumerate(station_indices):
        n1, n2 = frame_n1[int(idx)], frame_n2[int(idx)]
        origin = curve[int(idx)]
        for ai in range(angles):
            theta = 2.0 * math.pi * ai / angles
            direction = math.cos(theta) * n1 + math.sin(theta) * n2
            for rho in rhos:
                probes.append(origin + rho * direction)
                descriptors.append((si, ai, float(theta), float(rho)))
    return {
        "station_indices": station_indices,
        "rhos": rhos,
        "descriptors": descriptors,
        "probes": np.asarray(probes, dtype=float),
        "frame_mismatch": frame_mismatch,
    }


def _resolution_metrics(curve: np.ndarray, epsilon: float, target: float | None) -> dict[str, Any]:
    edges = np.linalg.norm(np.roll(curve, -1, axis=0) - curve, axis=1)
    mean_ratio = float(edges.mean() / epsilon)
    max_ratio = float(edges.max() / epsilon)
    target_met = None if target is None else mean_ratio <= target
    max_target_met = None if target is None else max_ratio <= target
    classification = "NOT_ASSESSED"
    if target is not None:
        classification = "TARGET_MET" if target_met else "UNDERRESOLVED_AGAINST_TARGET"
    return {
        "epsilon_over_rc": epsilon,
        "edge_length_mean_over_rc": float(edges.mean()),
        "edge_length_max_over_rc": float(edges.max()),
        "mean_ds_over_epsilon": mean_ratio,
        "max_ds_over_epsilon": max_ratio,
        "target_ds_over_epsilon": target,
        "target_met": target_met,
        "max_edge_target_met": max_target_met,
        "classification": classification,
        "guard": "A segment/softening ratio target is a discretization gate, not a proof of continuum convergence.",
    }


def _analyze_probe_field(
    *,
    curve: np.ndarray,
    knot_info: dict[str, Any],
    geometry: dict[str, Any],
    beta_vectors_arr: np.ndarray,
    backend: dict[str, Any],
    epsilon: float,
    kernel_model: str,
    stations: int,
    angles: int,
    rho_min: float,
    rho_max: float,
    radial_samples: int,
    resolution_target: float | None,
) -> dict[str, Any]:
    descriptors = geometry["descriptors"]
    station_indices = geometry["station_indices"]
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
    ray_diag = {
        "ray_count": len(per_ray),
        "interior_minimum_ray_count": 0,
        "lower_boundary_minimum_ray_count": 0,
        "upper_boundary_minimum_ray_count": 0,
        "all_invalid_ray_count": 0,
    }
    for (si, ai), values in per_ray.items():
        arr = np.asarray(values, dtype=float)
        xs, ys, bs = arr[:, 0], arr[:, 1], arr[:, 2]
        finite = np.isfinite(ys)
        if not np.any(finite):
            ray_diag["all_invalid_ray_count"] += 1
            continue
        finite_indices = np.flatnonzero(finite)
        min_index = int(finite_indices[np.argmin(ys[finite])])
        if min_index == 0:
            ray_diag["lower_boundary_minimum_ray_count"] += 1
        elif min_index == len(xs) - 1:
            ray_diag["upper_boundary_minimum_ray_count"] += 1
        else:
            ray_diag["interior_minimum_ray_count"] += 1
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
        curve,
        knot_info.get("knot_id")
        if knot_info.get("centerline_source") == "uploaded_ideal_fourier_catalog"
        else None,
    )
    beta_max_i = int(np.argmax(beta_mag)) if len(beta_mag) else 0
    beta_max_desc = descriptors[beta_max_i] if descriptors else (0, 0, 0.0, 0.0)
    resolution = _resolution_metrics(curve, epsilon, resolution_target)
    return {
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
            "kernel_model": kernel_model,
        },
        "kernel_reference": rosenhead_reference_regime(epsilon),
        "centerline_resolution": resolution,
        "frame_transport": {
            "method": "discrete_Bishop_parallel_transport",
            "closure_mismatch_rad": geometry["frame_mismatch"],
            "physical_twist_certified": False,
        },
        "field_summary": {
            "beta_min": float(beta_mag.min()) if len(beta_mag) else None,
            "beta_max": float(beta_mag.max()) if len(beta_mag) else None,
            "beta_mean": float(beta_mag.mean()) if len(beta_mag) else None,
            "beta_rms": float(math.sqrt(float(np.mean(beta_mag * beta_mag)))) if len(beta_mag) else None,
            "vector_component_sums": beta_vectors_arr.sum(axis=0).tolist() if len(beta_mag) else [0.0, 0.0, 0.0],
            "beta_max_probe": {
                "station": int(beta_max_desc[0]),
                "angle_index": int(beta_max_desc[1]),
                "theta_rad": float(beta_max_desc[2]),
                "rho_over_rc": float(beta_max_desc[3]),
            } if len(beta_mag) else None,
        },
        "ray_diagnostics": ray_diag,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "invalid_clock_probe_count": invalid_clock,
        "probe_count": int(len(geometry["probes"])),
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
        "guard": (
            "Local minima of rho/S in selected normal planes are not equivalent to "
            "closed Fermat geodesics in the full non-axisymmetric metric."
        ),
    }


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
    kernel_model: str,
    force_python: bool,
    auto_build: bool,
    resolution_target: float | None = None,
) -> tuple[dict[str, Any], np.ndarray]:
    if kernel_model not in KERNEL_MODELS:
        raise ValueError(f"unknown kernel_model={kernel_model}; available={KERNEL_MODELS}")
    curve = np.asarray(curve, dtype=float)
    geometry = _build_probe_geometry(
        curve,
        stations=stations,
        angles=angles,
        rho_min=rho_min,
        rho_max=rho_max,
        radial_samples=radial_samples,
    )
    beta_vectors, backend = backend_biot_savart(
        curve.tolist(),
        geometry["probes"].tolist(),
        epsilon=epsilon,
        kernel_model=kernel_model,
        force_python=force_python,
        auto_build=auto_build,
    )
    beta_vectors_arr = np.asarray(beta_vectors, dtype=float)
    result = _analyze_probe_field(
        curve=curve,
        knot_info=knot_info,
        geometry=geometry,
        beta_vectors_arr=beta_vectors_arr,
        backend=backend,
        epsilon=epsilon,
        kernel_model=kernel_model,
        stations=stations,
        angles=angles,
        rho_min=rho_min,
        rho_max=rho_max,
        radial_samples=radial_samples,
        resolution_target=resolution_target,
    )
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
    kernel_model: str = "rosenhead_midpoint",
    resolution_target: float | None = None,
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
        curve=curve,
        knot_info=info,
        stations=stations,
        angles=angles,
        rho_min=rho_min,
        rho_max=rho_max,
        radial_samples=radial_samples,
        epsilon=epsilon,
        kernel_model=kernel_model,
        force_python=force_python,
        auto_build=auto_build,
        resolution_target=resolution_target,
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
    kernel_model: str = "rosenhead_midpoint",
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
        stations=stations,
        angles=angles,
        rho_min=rho_min,
        rho_max=rho_max,
        radial_samples=radial_samples,
        epsilon=epsilon,
        kernel_model=kernel_model,
        force_python=force_python,
        auto_build=auto_build,
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


def _parity_metrics(
    primary_result: dict[str, Any],
    primary_beta: np.ndarray,
    python_result: dict[str, Any],
    python_beta: np.ndarray,
) -> dict[str, Any]:
    vector_linf = float(np.max(np.abs(primary_beta - python_beta))) if len(primary_beta) else 0.0
    magnitude_linf = float(
        np.max(np.abs(np.linalg.norm(primary_beta, axis=1) - np.linalg.norm(python_beta, axis=1)))
    ) if len(primary_beta) else 0.0
    candidate_rho_error = _candidate_rho_parity(primary_result, python_result)
    native = primary_result["backend"]["backend"] == "cpp"
    parity_ok = (
        native
        and vector_linf < 1e-10
        and magnitude_linf < 1e-10
        and primary_result["candidate_count"] == python_result["candidate_count"]
        and primary_result["invalid_clock_probe_count"] == python_result["invalid_clock_probe_count"]
        and candidate_rho_error is not None
        and candidate_rho_error < 1e-10
    )
    return {
        "primary_backend": primary_result["backend"]["backend"],
        "native_available": native,
        "beta_vector_linf_error": vector_linf,
        "beta_magnitude_linf_error": magnitude_linf,
        "candidate_rho_linf_error": candidate_rho_error,
        "candidate_count_match": primary_result["candidate_count"] == python_result["candidate_count"],
        "invalid_clock_count_match": (
            primary_result["invalid_clock_probe_count"] == python_result["invalid_clock_probe_count"]
        ),
        "native_python_parity_ok": parity_ok,
    }


def _catalog_info(knot_id: str, scale_over_rc: float) -> dict[str, Any]:
    info = knot_metadata(knot_id)
    info.update({
        "centerline_source": "uploaded_ideal_fourier_catalog",
        "scale_over_rc": scale_over_rc,
        "uniform_arclength_resampled": True,
    })
    return info


def scan_catalog_matrix(
    knot_ids: Iterable[str] = DEFAULT_KNOT_IDS,
    *,
    centerline_points: int | None = 256,
    adaptive_resolution: bool = False,
    target_ds_over_epsilon: float = 1.0,
    min_centerline_points: int = 128,
    max_centerline_points: int = 8192,
    scale_over_rc: float = 1.0,
    stations: int = 8,
    angles: int = 12,
    rho_min: float = 0.002,
    rho_max: float = 0.05,
    radial_samples: int = 80,
    epsilon: float = 0.0045,
    kernel_model: str = "rosenhead_midpoint",
    auto_build: bool = True,
) -> dict[str, Any]:
    ids = validate_knot_ids(knot_ids)
    rows: list[dict[str, Any]] = []
    results: dict[str, dict[str, Any]] = {}

    for index, knot_id in enumerate(ids):
        plan = None
        if adaptive_resolution:
            plan = resolution_plan(
                knot_id,
                epsilon=epsilon,
                scale_over_rc=scale_over_rc,
                target_ds_over_epsilon=target_ds_over_epsilon,
                min_points=min_centerline_points,
                max_points=max_centerline_points,
            )
            n_points = int(plan["selected_points"])
        else:
            if centerline_points is None:
                raise ValueError("centerline_points is required when adaptive_resolution is false")
            n_points = int(centerline_points)
        curve = sample_ideal_knot(knot_id, n_points, scale_over_rc=scale_over_rc)
        info = _catalog_info(knot_id, scale_over_rc)
        py_result, py_beta = _scan_curve_raw(
            curve=curve,
            knot_info=info,
            stations=stations,
            angles=angles,
            rho_min=rho_min,
            rho_max=rho_max,
            radial_samples=radial_samples,
            epsilon=epsilon,
            kernel_model=kernel_model,
            force_python=True,
            auto_build=False,
            resolution_target=target_ds_over_epsilon if adaptive_resolution else None,
        )
        primary_result, primary_beta = _scan_curve_raw(
            curve=curve,
            knot_info=info,
            stations=stations,
            angles=angles,
            rho_min=rho_min,
            rho_max=rho_max,
            radial_samples=radial_samples,
            epsilon=epsilon,
            kernel_model=kernel_model,
            force_python=False,
            auto_build=auto_build if index == 0 else False,
            resolution_target=target_ds_over_epsilon if adaptive_resolution else None,
        )
        parity = _parity_metrics(primary_result, primary_beta, py_result, py_beta)
        row = {
            "knot_id": knot_id,
            "source_id": info["source_id"],
            "source_length_L": info["source_length_L"],
            "coefficient_count": info["coefficient_count"],
            "epsilon_over_rc": epsilon,
            "kernel_model": kernel_model,
            "centerline_points": n_points,
            "adaptive_resolution": adaptive_resolution,
            "resolution_plan_classification": plan["classification"] if plan else "FIXED_POINT_COUNT",
            "mean_ds_over_epsilon": primary_result["centerline_resolution"]["mean_ds_over_epsilon"],
            "max_ds_over_epsilon": primary_result["centerline_resolution"]["max_ds_over_epsilon"],
            "resolution_target_met": primary_result["centerline_resolution"]["target_met"],
            "probe_count": primary_result["probe_count"],
            "candidate_count_primary": primary_result["candidate_count"],
            "candidate_count_python": py_result["candidate_count"],
            "invalid_clock_primary": primary_result["invalid_clock_probe_count"],
            "invalid_clock_python": py_result["invalid_clock_probe_count"],
            "beta_max_primary": primary_result["field_summary"]["beta_max"],
            "source_length_relative_error": primary_result["centerline"]["source_length_relative_error"],
            **parity,
            "global_closed_orbit_certified": False,
            "qsm_certified": False,
        }
        rows.append(row)
        results[knot_id] = {
            "resolution_plan": plan,
            "primary": primary_result,
            "python": py_result,
            "parity": parity,
        }

    native_all = all(row["native_available"] for row in rows)
    parity_all = native_all and all(row["native_python_parity_ok"] for row in rows)
    return {
        "schema": "sst.fermat.knot-matrix.v0.4.1",
        "package_version": PACKAGE_VERSION,
        "status": "RESEARCH_TRACK_DIAGNOSTIC_ONLY",
        "knot_ids": list(ids),
        "settings": {
            "centerline_points": centerline_points,
            "adaptive_resolution": adaptive_resolution,
            "target_ds_over_epsilon": target_ds_over_epsilon,
            "min_centerline_points": min_centerline_points,
            "max_centerline_points": max_centerline_points,
            "scale_over_rc": scale_over_rc,
            "stations": stations,
            "angles": angles,
            "rho_min_over_rc": rho_min,
            "rho_max_over_rc": rho_max,
            "radial_samples": radial_samples,
            "biot_savart_softening_over_rc": epsilon,
            "kernel_model": kernel_model,
        },
        "kernel_reference": rosenhead_reference_regime(epsilon),
        "rows": rows,
        "results": results,
        "native_available_for_all_knots": native_all,
        "native_python_parity_certified_for_all_knots": parity_all,
        "resolution_target_met_for_all_knots": (
            all(row["resolution_target_met"] is True for row in rows) if adaptive_resolution else None
        ),
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }


def scan_softening_matrix(
    knot_ids: Iterable[str] = DEFAULT_KNOT_IDS,
    *,
    epsilon_values: Sequence[float],
    target_ds_over_epsilon: float = 1.0,
    min_centerline_points: int = 128,
    max_centerline_points: int = 8192,
    scale_over_rc: float = 1.0,
    stations: int = 4,
    angles: int = 12,
    rho_min: float = 0.0005,
    rho_max: float = 0.03,
    radial_samples: int = 96,
    kernel_model: str = "rosenhead_midpoint",
    parity_mode: str = "spot",
    parity_stations: int = 2,
    parity_angles: int = 4,
    parity_radial_samples: int = 24,
    auto_build: bool = True,
) -> dict[str, Any]:
    ids = validate_knot_ids(knot_ids)
    eps_values = [float(v) for v in epsilon_values]
    if not eps_values or any(v <= 0.0 for v in eps_values):
        raise ValueError("epsilon_values must contain positive values")
    if parity_mode not in {"full", "spot", "none"}:
        raise ValueError("parity_mode must be full, spot, or none")

    rows: list[dict[str, Any]] = []
    results: dict[str, Any] = {}
    first_primary = True
    for epsilon in eps_values:
        eps_key = f"{epsilon:.10g}"
        results[eps_key] = {}
        for knot_id in ids:
            plan = resolution_plan(
                knot_id,
                epsilon=epsilon,
                scale_over_rc=scale_over_rc,
                target_ds_over_epsilon=target_ds_over_epsilon,
                min_points=min_centerline_points,
                max_points=max_centerline_points,
            )
            n_points = int(plan["selected_points"])
            curve = sample_ideal_knot(knot_id, n_points, scale_over_rc=scale_over_rc)
            info = _catalog_info(knot_id, scale_over_rc)
            primary_result, primary_beta = _scan_curve_raw(
                curve=curve,
                knot_info=info,
                stations=stations,
                angles=angles,
                rho_min=rho_min,
                rho_max=rho_max,
                radial_samples=radial_samples,
                epsilon=epsilon,
                kernel_model=kernel_model,
                force_python=False,
                auto_build=auto_build if first_primary else False,
                resolution_target=target_ds_over_epsilon,
            )
            first_primary = False
            parity: dict[str, Any] = {
                "mode": parity_mode,
                "native_available": primary_result["backend"]["backend"] == "cpp",
                "native_python_parity_ok": None,
            }
            python_result = None
            if parity_mode == "full":
                python_result, python_beta = _scan_curve_raw(
                    curve=curve,
                    knot_info=info,
                    stations=stations,
                    angles=angles,
                    rho_min=rho_min,
                    rho_max=rho_max,
                    radial_samples=radial_samples,
                    epsilon=epsilon,
                    kernel_model=kernel_model,
                    force_python=True,
                    auto_build=False,
                    resolution_target=target_ds_over_epsilon,
                )
                parity.update(_parity_metrics(primary_result, primary_beta, python_result, python_beta))
            elif parity_mode == "spot":
                spot_primary, spot_primary_beta = _scan_curve_raw(
                    curve=curve,
                    knot_info=info,
                    stations=parity_stations,
                    angles=parity_angles,
                    rho_min=rho_min,
                    rho_max=rho_max,
                    radial_samples=parity_radial_samples,
                    epsilon=epsilon,
                    kernel_model=kernel_model,
                    force_python=False,
                    auto_build=False,
                    resolution_target=target_ds_over_epsilon,
                )
                spot_python, spot_python_beta = _scan_curve_raw(
                    curve=curve,
                    knot_info=info,
                    stations=parity_stations,
                    angles=parity_angles,
                    rho_min=rho_min,
                    rho_max=rho_max,
                    radial_samples=parity_radial_samples,
                    epsilon=epsilon,
                    kernel_model=kernel_model,
                    force_python=True,
                    auto_build=False,
                    resolution_target=target_ds_over_epsilon,
                )
                parity.update(_parity_metrics(spot_primary, spot_primary_beta, spot_python, spot_python_beta))
                parity["spot_probe_count"] = spot_primary["probe_count"]
            row = {
                "epsilon_over_rc": epsilon,
                "epsilon_regime": primary_result["kernel_reference"]["classification"],
                "knot_id": knot_id,
                "centerline_points": n_points,
                "resolution_plan_classification": plan["classification"],
                "mean_ds_over_epsilon": primary_result["centerline_resolution"]["mean_ds_over_epsilon"],
                "max_ds_over_epsilon": primary_result["centerline_resolution"]["max_ds_over_epsilon"],
                "resolution_target_met": primary_result["centerline_resolution"]["target_met"],
                "primary_backend": primary_result["backend"]["backend"],
                "native_available": primary_result["backend"]["backend"] == "cpp",
                "probe_count": primary_result["probe_count"],
                "candidate_count": primary_result["candidate_count"],
                "invalid_clock_probe_count": primary_result["invalid_clock_probe_count"],
                "beta_max": primary_result["field_summary"]["beta_max"],
                "lower_boundary_minimum_rays": primary_result["ray_diagnostics"]["lower_boundary_minimum_ray_count"],
                "interior_minimum_rays": primary_result["ray_diagnostics"]["interior_minimum_ray_count"],
                "parity_mode": parity_mode,
                "native_python_parity_ok": parity.get("native_python_parity_ok"),
                "beta_vector_linf_error": parity.get("beta_vector_linf_error"),
                "global_closed_orbit_certified": False,
                "qsm_certified": False,
            }
            rows.append(row)
            results[eps_key][knot_id] = {
                "resolution_plan": plan,
                "primary": primary_result,
                "python": python_result,
                "parity": parity,
            }

    native_all = all(row["native_available"] for row in rows)
    parity_rows = [row for row in rows if row["native_python_parity_ok"] is not None]
    parity_all = bool(parity_rows) and native_all and all(row["native_python_parity_ok"] for row in parity_rows)
    return {
        "schema": "sst.fermat.softening-matrix.v0.4.1",
        "package_version": PACKAGE_VERSION,
        "status": "RESEARCH_TRACK_DIAGNOSTIC_ONLY",
        "knot_ids": list(ids),
        "epsilon_values_over_rc": eps_values,
        "settings": {
            "target_ds_over_epsilon": target_ds_over_epsilon,
            "min_centerline_points": min_centerline_points,
            "max_centerline_points": max_centerline_points,
            "scale_over_rc": scale_over_rc,
            "stations": stations,
            "angles": angles,
            "rho_min_over_rc": rho_min,
            "rho_max_over_rc": rho_max,
            "radial_samples": radial_samples,
            "kernel_model": kernel_model,
            "parity_mode": parity_mode,
        },
        "straight_reference_thresholds": {
            "horizon_threshold_epsilon_over_rc": constants.ROSENHEAD_HORIZON_THRESHOLD,
            "critical_threshold_epsilon_over_rc": constants.ROSENHEAD_CRITICAL_THRESHOLD,
        },
        "rows": rows,
        "results": results,
        "native_available_for_all_rows": native_all,
        "native_python_parity_certified_for_checked_rows": parity_all if parity_mode != "none" else None,
        "resolution_target_met_for_all_rows": all(row["resolution_target_met"] is True for row in rows),
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }


def field_convergence_ladder(
    knot_ids: Iterable[str] = DEFAULT_KNOT_IDS,
    *,
    epsilon: float,
    point_counts: Sequence[int],
    scale_over_rc: float = 1.0,
    stations: int = 2,
    angles: int = 8,
    rho_min: float = 0.001,
    rho_max: float = 0.02,
    radial_samples: int = 32,
    kernel_model: str = "rosenhead_midpoint",
    auto_build: bool = True,
) -> dict[str, Any]:
    ids = validate_knot_ids(knot_ids)
    counts = sorted(set(int(v) for v in point_counts))
    if not counts or counts[0] < 16:
        raise ValueError("point_counts must contain integers >=16")
    rows: list[dict[str, Any]] = []
    results: dict[str, Any] = {}
    first_primary = True

    for knot_id in ids:
        reference_n = counts[-1]
        reference_curve = sample_ideal_knot(knot_id, reference_n, scale_over_rc=scale_over_rc)
        geometry = _build_probe_geometry(
            reference_curve,
            stations=stations,
            angles=angles,
            rho_min=rho_min,
            rho_max=rho_max,
            radial_samples=radial_samples,
        )
        probes = geometry["probes"].tolist()
        vectors_by_n: dict[int, np.ndarray] = {}
        backend_by_n: dict[int, dict[str, Any]] = {}
        for n_points in counts:
            curve = sample_ideal_knot(knot_id, n_points, scale_over_rc=scale_over_rc)
            vectors, backend = backend_biot_savart(
                curve.tolist(),
                probes,
                epsilon=epsilon,
                kernel_model=kernel_model,
                force_python=False,
                auto_build=auto_build if first_primary else False,
            )
            first_primary = False
            vectors_by_n[n_points] = np.asarray(vectors, dtype=float)
            backend_by_n[n_points] = backend
        reference = vectors_by_n[reference_n]
        py_reference, _ = backend_biot_savart(
            reference_curve.tolist(),
            probes,
            epsilon=epsilon,
            kernel_model=kernel_model,
            force_python=True,
            auto_build=False,
        )
        py_reference_arr = np.asarray(py_reference, dtype=float)
        native_reference = backend_by_n[reference_n]["backend"] == "cpp"
        parity_error = float(np.max(np.abs(reference - py_reference_arr)))
        knot_rows: list[dict[str, Any]] = []
        for n_points in counts:
            curve = sample_ideal_knot(knot_id, n_points, scale_over_rc=scale_over_rc)
            resolution = _resolution_metrics(curve, epsilon, None)
            vectors = vectors_by_n[n_points]
            vector_linf = float(np.max(np.abs(vectors - reference)))
            magnitude_linf = float(
                np.max(np.abs(np.linalg.norm(vectors, axis=1) - np.linalg.norm(reference, axis=1)))
            )
            row = {
                "knot_id": knot_id,
                "epsilon_over_rc": epsilon,
                "centerline_points": n_points,
                "reference_centerline_points": reference_n,
                "primary_backend": backend_by_n[n_points]["backend"],
                "mean_ds_over_epsilon": resolution["mean_ds_over_epsilon"],
                "max_ds_over_epsilon": resolution["max_ds_over_epsilon"],
                "beta_vector_linf_vs_reference": vector_linf,
                "beta_magnitude_linf_vs_reference": magnitude_linf,
                "is_reference_row": n_points == reference_n,
            }
            rows.append(row)
            knot_rows.append(row)
        results[knot_id] = {
            "reference_probe_count": len(probes),
            "reference_frame_mismatch_rad": geometry["frame_mismatch"],
            "reference_native_available": native_reference,
            "reference_native_python_linf_error": parity_error,
            "reference_native_python_parity_ok": native_reference and parity_error < 1e-10,
            "rows": knot_rows,
        }

    return {
        "schema": "sst.fermat.field-convergence.v0.4.1",
        "package_version": PACKAGE_VERSION,
        "status": "RESEARCH_TRACK_NUMERICAL_CONVERGENCE",
        "knot_ids": list(ids),
        "settings": {
            "epsilon_over_rc": epsilon,
            "point_counts": counts,
            "scale_over_rc": scale_over_rc,
            "stations": stations,
            "angles": angles,
            "rho_min_over_rc": rho_min,
            "rho_max_over_rc": rho_max,
            "radial_samples": radial_samples,
            "kernel_model": kernel_model,
        },
        "rows": rows,
        "results": results,
        "native_python_parity_certified_for_all_references": all(
            result["reference_native_python_parity_ok"] for result in results.values()
        ),
        "continuum_convergence_certified": False,
        "guard": (
            "The highest point count is used as a finite-resolution reference. "
            "Agreement with it is not an independent continuum proof."
        ),
    }
