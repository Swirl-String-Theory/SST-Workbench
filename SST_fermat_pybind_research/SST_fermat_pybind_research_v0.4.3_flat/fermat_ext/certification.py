from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

import numpy as np

from . import constants
from .core import PACKAGE_VERSION, backend_biot_savart_with_jacobian
from .knot_catalog import DEFAULT_KNOT_IDS, centerline_summary, knot_metadata, sample_ideal_knot, validate_knot_ids
from .knot_scan import parallel_transport_frames, rosenhead_reference_regime


@dataclass(frozen=True)
class Ray:
    ray_index: int
    station: int
    centerline_index: int
    station_fraction: float
    angle_index: int
    theta_rad: float
    origin: np.ndarray
    radial_direction: np.ndarray
    azimuthal_direction: np.ndarray


def _as_array3(values: Any) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise ValueError("expected shape (N,3)")
    return arr


def build_rays(curve: np.ndarray, *, stations: int, angles: int) -> tuple[list[Ray], dict[str, Any]]:
    if stations < 1 or angles < 3:
        raise ValueError("stations>=1 and angles>=3 required")
    curve = _as_array3(curve)
    tangents, n1, n2, mismatch = parallel_transport_frames(curve)
    station_indices = np.floor(np.arange(stations) * len(curve) / stations).astype(int)
    rays: list[Ray] = []
    for si, idx_raw in enumerate(station_indices):
        idx = int(idx_raw)
        for ai in range(angles):
            theta = 2.0 * math.pi * ai / angles
            er = math.cos(theta) * n1[idx] + math.sin(theta) * n2[idx]
            etheta = -math.sin(theta) * n1[idx] + math.cos(theta) * n2[idx]
            rays.append(Ray(
                ray_index=len(rays),
                station=si,
                centerline_index=idx,
                station_fraction=float(idx / len(curve)),
                angle_index=ai,
                theta_rad=theta,
                origin=curve[idx].copy(),
                radial_direction=er.copy(),
                azimuthal_direction=etheta.copy(),
            ))
    return rays, {
        "method": "discrete_Bishop_parallel_transport",
        "closure_mismatch_rad": mismatch,
        "station_indices": station_indices.tolist(),
        "physical_twist_certified": False,
        "tangent_count": len(tangents),
    }


def _field_quantities(
    beta: np.ndarray,
    jacobian: np.ndarray,
    directions: np.ndarray,
    rhos: np.ndarray,
) -> dict[str, np.ndarray]:
    beta = np.asarray(beta, dtype=float)
    jacobian = np.asarray(jacobian, dtype=float)
    directions = np.asarray(directions, dtype=float)
    rhos = np.asarray(rhos, dtype=float)
    beta2 = np.einsum("ij,ij->i", beta, beta)
    s2 = 1.0 - beta2
    clock_valid = s2 > 0.0
    d_beta_drho = np.einsum("nij,nj->ni", jacobian, directions)
    beta_dot_d = np.einsum("ij,ij->i", beta, d_beta_drho)
    g = s2 + rhos * beta_dot_d
    rf = np.full_like(rhos, np.nan, dtype=float)
    d_rf = np.full_like(rhos, np.nan, dtype=float)
    s = np.full_like(rhos, np.nan, dtype=float)
    s[clock_valid] = np.sqrt(s2[clock_valid])
    rf[clock_valid] = rhos[clock_valid] / s[clock_valid]
    d_rf[clock_valid] = g[clock_valid] / np.power(s[clock_valid], 3)
    grad_s = np.full_like(beta, np.nan, dtype=float)
    if np.any(clock_valid):
        grad_s[clock_valid] = -np.einsum(
            "nji,nj->ni", jacobian[clock_valid], beta[clock_valid]
        ) / s[clock_valid, None]
    return {
        "beta2": beta2,
        "S2": s2,
        "S": s,
        "clock_valid": clock_valid,
        "d_beta_drho": d_beta_drho,
        "beta_dot_d_beta_drho": beta_dot_d,
        "G": g,
        "R_F": rf,
        "d_R_F_drho": d_rf,
        "grad_S": grad_s,
    }


def _evaluate_points(
    curve: np.ndarray,
    points: np.ndarray,
    directions: np.ndarray,
    rhos: np.ndarray,
    *,
    epsilon: float,
    kernel_model: str,
    force_python: bool,
    auto_build: bool,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    beta, jacobian, backend = backend_biot_savart_with_jacobian(
        curve.tolist(),
        np.asarray(points, dtype=float).tolist(),
        epsilon=epsilon,
        kernel_model=kernel_model,
        force_python=force_python,
        auto_build=auto_build,
    )
    beta_arr = np.asarray(beta, dtype=float)
    jac_arr = np.asarray(jacobian, dtype=float)
    q = _field_quantities(beta_arr, jac_arr, directions, rhos)
    q["beta"] = beta_arr
    q["jacobian"] = jac_arr
    return q, backend


def _root_brackets(
    g: np.ndarray,
    valid: np.ndarray,
    rhos: np.ndarray,
    *,
    roots_per_ray: int,
    ray_count: int,
    zero_tol: float,
) -> list[dict[str, Any]]:
    g2 = g.reshape(ray_count, roots_per_ray)
    v2 = valid.reshape(ray_count, roots_per_ray)
    brackets: list[dict[str, Any]] = []
    for ri in range(ray_count):
        for j in range(roots_per_ray - 1):
            if not (v2[ri, j] and v2[ri, j + 1]):
                continue
            gl = float(g2[ri, j])
            gh = float(g2[ri, j + 1])
            if not (math.isfinite(gl) and math.isfinite(gh)):
                continue
            if abs(gl) <= zero_tol:
                lo = max(0, j - 1)
                hi = min(roots_per_ray - 1, j + 1)
                if lo != hi and v2[ri, lo] and v2[ri, hi]:
                    brackets.append({"ray_index": ri, "lo": float(rhos[lo]), "hi": float(rhos[hi]),
                                     "g_lo": float(g2[ri, lo]), "g_hi": float(g2[ri, hi])})
                continue
            if gl * gh < 0.0:
                brackets.append({"ray_index": ri, "lo": float(rhos[j]), "hi": float(rhos[j + 1]),
                                 "g_lo": gl, "g_hi": gh})
    # De-duplicate brackets that share the same ray and overlap around a sampled zero.
    brackets.sort(key=lambda b: (b["ray_index"], b["lo"], b["hi"]))
    unique: list[dict[str, Any]] = []
    for b in brackets:
        if unique and b["ray_index"] == unique[-1]["ray_index"] and b["lo"] <= unique[-1]["hi"]:
            if (b["hi"] - b["lo"]) < (unique[-1]["hi"] - unique[-1]["lo"]):
                unique[-1] = b
        else:
            unique.append(b)
    return unique


def _refine_brackets_batch(
    curve: np.ndarray,
    rays: Sequence[Ray],
    brackets: list[dict[str, Any]],
    *,
    epsilon: float,
    kernel_model: str,
    force_python: bool,
    auto_build: bool,
    root_abs_tol: float,
    root_rel_tol: float,
    max_iterations: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not brackets:
        return [], {"backend": "none", "build": None, "import_error": None}
    backend: dict[str, Any] | None = None
    active = [dict(b) for b in brackets]
    for b in active:
        b["discard_reason"] = None
    for _ in range(max_iterations):
        mids = np.asarray([0.5 * (b["lo"] + b["hi"]) for b in active], dtype=float)
        widths = np.asarray([b["hi"] - b["lo"] for b in active], dtype=float)
        discarded = np.asarray([b.get("discard_reason") is not None for b in active], dtype=bool)
        done = (
            widths <= np.maximum(root_abs_tol, root_rel_tol * np.maximum(mids, 1e-30))
        ) | discarded
        if bool(np.all(done)):
            break
        points = np.asarray([
            rays[int(b["ray_index"])].origin + mid * rays[int(b["ray_index"])].radial_direction
            for b, mid in zip(active, mids)
        ])
        dirs = np.asarray([rays[int(b["ray_index"])].radial_direction for b in active])
        q, backend_now = _evaluate_points(
            curve, points, dirs, mids,
            epsilon=epsilon, kernel_model=kernel_model,
            force_python=force_python, auto_build=auto_build if backend is None else False,
        )
        if backend is None:
            backend = backend_now
        for i, b in enumerate(active):
            if done[i]:
                continue
            gm = float(q["G"][i])
            if not bool(q["clock_valid"][i]) or not math.isfinite(gm):
                b["invalid_during_refinement"] = True
                # Bisection is valid only on a connected clock-valid interval.  If a
                # clock-invalid midpoint appears between valid sampled endpoints, the
                # bracket straddles an unresolved domain break and must not be certified.
                b["discard_reason"] = "CLOCK_INVALID_DURING_REFINEMENT"
                continue
            if b["g_lo"] * gm <= 0.0:
                b["hi"] = float(mids[i])
                b["g_hi"] = gm
            else:
                b["lo"] = float(mids[i])
                b["g_lo"] = gm
    # Reject brackets whose refinement crossed a clock-invalid subinterval.  A
    # sign change across a disconnected physical domain is not a certifiable root.
    resolved = [b for b in active if b.get("discard_reason") is None]
    if not resolved:
        return [], backend or {"backend": "none", "build": None, "import_error": None}

    roots = []
    root_rhos = np.asarray([0.5 * (b["lo"] + b["hi"]) for b in resolved], dtype=float)
    root_points = np.asarray([
        rays[int(b["ray_index"])].origin + rho * rays[int(b["ray_index"])].radial_direction
        for b, rho in zip(resolved, root_rhos)
    ])
    root_dirs = np.asarray([rays[int(b["ray_index"])].radial_direction for b in resolved])
    q, backend_now = _evaluate_points(
        curve, root_points, root_dirs, root_rhos,
        epsilon=epsilon, kernel_model=kernel_model,
        force_python=force_python, auto_build=auto_build if backend is None else False,
    )
    if backend is None:
        backend = backend_now

    # Evaluate both final bracket endpoints.  The previous implementation divided
    # endpoint G-values by the root-point S^3.  Besides being mathematically
    # inconsistent, that produced a complex number when the root point was
    # clock-invalid.  Endpoint derivatives are now taken directly from the same
    # field evaluator that defines dR_F/drho.
    lo_rhos = np.asarray([b["lo"] for b in resolved], dtype=float)
    hi_rhos = np.asarray([b["hi"] for b in resolved], dtype=float)
    endpoint_rhos = np.concatenate([lo_rhos, hi_rhos])
    endpoint_points = np.asarray([
        rays[int(b["ray_index"])].origin + rho * rays[int(b["ray_index"])].radial_direction
        for b, rho in list(zip(resolved, lo_rhos)) + list(zip(resolved, hi_rhos))
    ])
    endpoint_dirs = np.asarray(
        [rays[int(b["ray_index"])].radial_direction for b in resolved] * 2
    )
    q_end, _ = _evaluate_points(
        curve, endpoint_points, endpoint_dirs, endpoint_rhos,
        epsilon=epsilon, kernel_model=kernel_model,
        force_python=force_python, auto_build=False,
    )
    n_resolved = len(resolved)

    for i, (b, rho) in enumerate(zip(resolved, root_rhos)):
        ray = rays[int(b["ray_index"])]
        root_clock_valid = bool(q["clock_valid"][i])
        endpoints_clock_valid = bool(q_end["clock_valid"][i]) and bool(
            q_end["clock_valid"][n_resolved + i]
        )
        gl = float(q_end["G"][i])
        gh = float(q_end["G"][n_resolved + i])
        if not root_clock_valid or not endpoints_clock_valid:
            classification = "CLOCK_INVALID"
        elif gl < 0.0 < gh:
            classification = "RESOLVED_LOCAL_MINIMUM"
        elif gl > 0.0 > gh:
            classification = "LOCAL_MAXIMUM"
        else:
            classification = "DEGENERATE_STATIONARY_POINT"
        s = float(q["S"][i]) if root_clock_valid else math.nan
        d_lo = float(q_end["d_R_F_drho"][i])
        d_hi = float(q_end["d_R_F_drho"][n_resolved + i])
        if math.isfinite(d_lo) and math.isfinite(d_hi):
            second_est: float | None = (d_hi - d_lo) / max(
                float(b["hi"] - b["lo"]), 1e-300
            )
        else:
            second_est = None
        roots.append({
            "ray_index": ray.ray_index,
            "station": ray.station,
            "centerline_index": ray.centerline_index,
            "station_fraction": ray.station_fraction,
            "angle_index": ray.angle_index,
            "theta_rad": ray.theta_rad,
            "rho_over_rc": float(rho),
            "r_m": float(rho * constants.R_C),
            "position_over_rc": root_points[i].tolist(),
            "radial_direction": ray.radial_direction.tolist(),
            "azimuthal_seed_direction": ray.azimuthal_direction.tolist(),
            "beta_vector": q["beta"][i].tolist(),
            "beta_magnitude": float(math.sqrt(max(float(q["beta2"][i]), 0.0))),
            "jacobian": q["jacobian"][i].tolist(),
            "grad_S": q["grad_S"][i].tolist(),
            "S": s if math.isfinite(s) else None,
            "R_F_over_rc": float(q["R_F"][i]) if math.isfinite(float(q["R_F"][i])) else None,
            "stationary_residual_G": float(q["G"][i]),
            "bracket_width_over_rc": float(b["hi"] - b["lo"]),
            "R_F_second_estimate": (
                float(second_est) if second_est is not None and math.isfinite(second_est) else None
            ),
            "clock_valid": bool(q["clock_valid"][i]),
            "classification": classification,
            "global_closed_orbit_certified": False,
        })
    roots.sort(key=lambda r: (r["station"], r["angle_index"], r["rho_over_rc"]))
    return roots, backend or {"backend": "unknown", "build": None, "import_error": None}


def estimate_reach_diagnostic(
    curve: np.ndarray,
    *,
    max_pair_points: int = 2048,
    tangent_perpendicular_tolerance: float = 0.05,
) -> dict[str, Any]:
    """Approximate reach diagnostic from curvature and nonlocal doubly-critical chords.

    This is intentionally labelled a diagnostic, not a rigorous reach certificate.  The
    pair search is performed on an arclength-uniform subsample and requires approximate
    perpendicularity to both local tangents.
    """
    c = _as_array3(curve)
    n = len(c)
    prev = np.roll(c, 1, axis=0)
    nxt = np.roll(c, -1, axis=0)
    a = np.linalg.norm(c - prev, axis=1)
    b = np.linalg.norm(nxt - c, axis=1)
    chord = np.linalg.norm(nxt - prev, axis=1)
    cross_area2 = np.linalg.norm(np.cross(c - prev, nxt - prev), axis=1)
    circumradius = np.full(n, np.inf)
    mask = cross_area2 > 1e-15
    circumradius[mask] = a[mask] * b[mask] * chord[mask] / (2.0 * cross_area2[mask])
    min_curvature_radius = float(np.min(circumradius))

    m = min(n, max_pair_points)
    indices = np.floor(np.arange(m) * n / m).astype(int)
    s = c[indices]
    tang = np.roll(s, -1, axis=0) - np.roll(s, 1, axis=0)
    tang /= np.linalg.norm(tang, axis=1)[:, None]
    exclusion = max(3, int(math.ceil(0.01 * m)))
    best = math.inf
    best_pair: tuple[int, int] | None = None
    best_perp = None
    chunk = 256
    for i0 in range(0, m, chunk):
        i1 = min(m, i0 + chunk)
        diff = s[i0:i1, None, :] - s[None, :, :]
        dist = np.linalg.norm(diff, axis=2)
        for ii in range(i1 - i0):
            i = i0 + ii
            circular_sep = np.minimum(np.abs(np.arange(m) - i), m - np.abs(np.arange(m) - i))
            dist[ii, circular_sep <= exclusion] = np.inf
        candidates = np.argwhere(dist < best)
        for ii, j in candidates:
            i = i0 + int(ii)
            j = int(j)
            d = float(dist[ii, j])
            if not math.isfinite(d) or d <= 0.0:
                continue
            u = (s[j] - s[i]) / d
            p1 = abs(float(np.dot(u, tang[i])))
            p2 = abs(float(np.dot(u, tang[j])))
            if p1 <= tangent_perpendicular_tolerance and p2 <= tangent_perpendicular_tolerance:
                best = d
                best_pair = (int(indices[i]), int(indices[j]))
                best_perp = (p1, p2)
    half_dcsd = 0.5 * best if math.isfinite(best) else math.inf
    reach = min(min_curvature_radius, half_dcsd)
    controller = "curvature" if min_curvature_radius <= half_dcsd else "approximate_dcsd"
    return {
        "method": "subsampled_curvature_plus_approximate_dcsd",
        "rigorous_certificate": False,
        "curve_points": n,
        "pair_search_points": m,
        "local_index_exclusion": exclusion,
        "tangent_perpendicular_tolerance": tangent_perpendicular_tolerance,
        "min_curvature_radius_over_rc": min_curvature_radius,
        "approximate_dcsd_over_rc": best if math.isfinite(best) else None,
        "half_approximate_dcsd_over_rc": half_dcsd if math.isfinite(half_dcsd) else None,
        "reach_estimate_over_rc": reach if math.isfinite(reach) else None,
        "controlling_term": controller,
        "dcsd_centerline_index_pair": list(best_pair) if best_pair else None,
        "dcsd_perpendicularity_residuals": list(best_perp) if best_perp else None,
    }



def _clock_domain_diagnostics(
    valid_grid: np.ndarray,
    rhos: np.ndarray,
    rays: Sequence[Ray],
) -> dict[str, Any]:
    """Describe connected real-clock components on every sampled normal ray.

    A transition in the Boolean clock-valid mask brackets ``S=0`` but is never
    treated as a stationary Fermat root.  Components are sampled-domain
    diagnostics: their endpoints are probe brackets, not refined horizon roots.
    """
    valid_grid = np.asarray(valid_grid, dtype=bool)
    rhos = np.asarray(rhos, dtype=float)
    if valid_grid.shape != (len(rays), len(rhos)):
        raise ValueError("valid_grid shape does not match rays and rhos")

    boundary_brackets: list[dict[str, Any]] = []
    split_rays: list[dict[str, Any]] = []
    component_count_by_ray: list[int] = []
    rays_with_any_valid: set[int] = set()
    fully_valid: set[int] = set()
    rays_with_boundary: set[int] = set()
    total_components = 0

    for ri, ray in enumerate(rays):
        mask = valid_grid[ri]
        if bool(np.any(mask)):
            rays_with_any_valid.add(ri)
        if bool(np.all(mask)):
            fully_valid.add(ri)

        transitions = np.flatnonzero(mask[:-1] != mask[1:])
        if len(transitions):
            rays_with_boundary.add(ri)
        for j_raw in transitions:
            j = int(j_raw)
            boundary_brackets.append({
                "ray_index": ri,
                "station": ray.station,
                "angle_index": ray.angle_index,
                "rho_lo_over_rc": float(rhos[j]),
                "rho_hi_over_rc": float(rhos[j + 1]),
                "valid_lo": bool(mask[j]),
                "valid_hi": bool(mask[j + 1]),
                "classification": "CLOCK_BOUNDARY_BRACKET",
            })

        components: list[dict[str, Any]] = []
        start: int | None = None
        for j, flag in enumerate(mask):
            if flag and start is None:
                start = j
            at_end = j == len(mask) - 1
            if start is not None and ((not flag) or at_end):
                end = j if flag and at_end else j - 1
                components.append({
                    "sample_index_start": int(start),
                    "sample_index_end": int(end),
                    "rho_start_over_rc": float(rhos[start]),
                    "rho_end_over_rc": float(rhos[end]),
                    "left_censored_by_scan_boundary": bool(start == 0),
                    "right_censored_by_scan_boundary": bool(end == len(mask) - 1),
                })
                start = None

        count = len(components)
        component_count_by_ray.append(count)
        total_components += count
        if count > 1:
            split_rays.append({
                "ray_index": ri,
                "station": ray.station,
                "angle_index": ray.angle_index,
                "real_clock_component_count": count,
                "components": components,
            })

    return {
        "valid_clock_ray_indices": sorted(rays_with_any_valid),
        "fully_clock_valid_ray_indices": sorted(fully_valid),
        "rays_with_clock_boundary_indices": sorted(rays_with_boundary),
        "clock_boundary_brackets": boundary_brackets,
        "clock_boundary_bracket_count": len(boundary_brackets),
        "real_clock_component_count_by_ray": component_count_by_ray,
        "real_clock_component_count_total": total_components,
        "rays_with_disconnected_clock_domain": len(split_rays),
        # Backward-compatible alias, now with an explicit and useful meaning.
        "clock_domain_split_count": len(split_rays),
        "clock_domain_splits": split_rays,
    }

def scan_stationary_candidates(
    knot_id: str,
    *,
    epsilon: float,
    centerline_points: int,
    scale_over_rc: float = 1.0,
    stations: int = 8,
    angles: int = 16,
    rho_min: float = 5e-4,
    rho_max: float = 0.03,
    bracket_samples: int = 96,
    kernel_model: str = "rosenhead_midpoint",
    root_abs_tol: float = 1e-11,
    root_rel_tol: float = 1e-9,
    root_zero_tol: float = 1e-9,
    max_root_iterations: int = 80,
    force_python: bool = False,
    auto_build: bool = True,
    reach_pair_points: int = 2048,
    reach_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validate_knot_ids([knot_id])
    if centerline_points < 16:
        raise ValueError("centerline_points>=16 required")
    if not (0 < rho_min < rho_max):
        raise ValueError("require 0<rho_min<rho_max")
    if bracket_samples < 8:
        raise ValueError("bracket_samples>=8 required")
    curve = sample_ideal_knot(knot_id, centerline_points, scale_over_rc=scale_over_rc)
    rays, frame = build_rays(curve, stations=stations, angles=angles)
    rhos = np.geomspace(rho_min, rho_max, bracket_samples)
    points = np.asarray([ray.origin + rho * ray.radial_direction for ray in rays for rho in rhos])
    directions = np.asarray([ray.radial_direction for ray in rays for _ in rhos])
    tiled_rhos = np.tile(rhos, len(rays))
    q, backend = _evaluate_points(
        curve, points, directions, tiled_rhos,
        epsilon=epsilon, kernel_model=kernel_model,
        force_python=force_python, auto_build=auto_build,
    )
    brackets = _root_brackets(
        q["G"], q["clock_valid"], rhos,
        roots_per_ray=len(rhos), ray_count=len(rays), zero_tol=root_zero_tol,
    )
    roots, root_backend = _refine_brackets_batch(
        curve, rays, brackets,
        epsilon=epsilon, kernel_model=kernel_model,
        force_python=force_python, auto_build=False,
        root_abs_tol=root_abs_tol, root_rel_tol=root_rel_tol,
        max_iterations=max_root_iterations,
    )
    if backend.get("backend") != root_backend.get("backend") and roots:
        raise RuntimeError("backend changed during candidate refinement")
    reach = reach_override if reach_override is not None else estimate_reach_diagnostic(
        curve, max_pair_points=reach_pair_points
    )
    reach_value = reach.get("reach_estimate_over_rc")
    for root in roots:
        root["inside_approximate_reach"] = (
            bool(root["rho_over_rc"] < reach_value) if reach_value is not None else None
        )
        if root["classification"] == "RESOLVED_LOCAL_MINIMUM" and root["inside_approximate_reach"] is False:
            root["classification"] = "GLOBAL_CAUSTIC_REGIME"
    rays_with_min: set[int] = set()
    valid_grid = q["clock_valid"].reshape(len(rays), len(rhos))
    clock_diag = _clock_domain_diagnostics(valid_grid, rhos, rays)
    valid_clock_rays = set(clock_diag["valid_clock_ray_indices"])
    fully_clock_valid_rays = set(clock_diag["fully_clock_valid_ray_indices"])
    for root in roots:
        if root["classification"] in {"RESOLVED_LOCAL_MINIMUM", "GLOBAL_CAUSTIC_REGIME"}:
            rays_with_min.add(int(root["ray_index"]))
    rays_with_min_and_valid = rays_with_min.intersection(valid_clock_rays)
    rays_with_min_and_fully_valid = rays_with_min.intersection(fully_clock_valid_rays)
    min_roots = [r for r in roots if r["classification"] == "RESOLVED_LOCAL_MINIMUM"]
    surface_fraction_valid_rays = (
        len(rays_with_min_and_valid) / len(valid_clock_rays) if valid_clock_rays else None
    )
    surface_fraction_all_rays = len(rays_with_min) / len(rays)
    surface_fraction_fully_valid = (
        len(rays_with_min_and_fully_valid) / len(fully_clock_valid_rays)
        if fully_clock_valid_rays else None
    )
    return {
        "schema": "sst.fermat.candidate-atlas.v0.4.3",
        "package_version": PACKAGE_VERSION,
        "status": "RESEARCH_TRACK_STATIONARY_ROOT_RESOLUTION",
        "knot_id": knot_id,
        "source": knot_metadata(knot_id),
        "backend": backend,
        "settings": {
            "epsilon_over_rc": epsilon,
            "kernel_model": kernel_model,
            "centerline_points": centerline_points,
            "scale_over_rc": scale_over_rc,
            "stations": stations,
            "angles": angles,
            "rho_min_over_rc": rho_min,
            "rho_max_over_rc": rho_max,
            "bracket_samples": bracket_samples,
            "root_abs_tol": root_abs_tol,
            "root_rel_tol": root_rel_tol,
        },
        "kernel_reference": rosenhead_reference_regime(epsilon),
        "centerline": centerline_summary(curve, knot_id),
        "frame_transport": frame,
        "reach_diagnostic": reach,
        "ray_count": len(rays),
        "valid_clock_ray_count": len(valid_clock_rays),
        "fully_clock_valid_ray_count": len(fully_clock_valid_rays),
        "rays_with_clock_boundary_count": len(clock_diag["rays_with_clock_boundary_indices"]),
        "invalid_clock_probe_count": int(np.count_nonzero(~q["clock_valid"])),
        "clock_boundary_bracket_count": clock_diag["clock_boundary_bracket_count"],
        "clock_boundary_brackets": clock_diag["clock_boundary_brackets"],
        "real_clock_component_count_by_ray": clock_diag["real_clock_component_count_by_ray"],
        "real_clock_component_count_total": clock_diag["real_clock_component_count_total"],
        "rays_with_disconnected_clock_domain": clock_diag["rays_with_disconnected_clock_domain"],
        "clock_domain_split_count": clock_diag["clock_domain_split_count"],
        "clock_domain_splits": clock_diag["clock_domain_splits"],
        "bracket_count": len(brackets),
        "stationary_root_count": len(roots),
        "local_minimum_count": len(min_roots),
        "rays_with_local_minimum_count": len(rays_with_min),
        "rays_with_local_minimum_and_fully_clock_valid_count": len(rays_with_min_and_fully_valid),
        "candidate_surface_fraction": surface_fraction_valid_rays,
        "candidate_surface_fraction_valid_clock_rays": surface_fraction_valid_rays,
        "candidate_surface_fraction_all_rays": surface_fraction_all_rays,
        "candidate_surface_fraction_fully_clock_valid_rays": surface_fraction_fully_valid,
        "candidate_surface_fraction_definition": (
            "candidate_surface_fraction is normalized by rays containing at least one real-clock "
            "probe. candidate_surface_fraction_all_rays is P_all in [0,1]. The fully-clock-valid "
            "conditional fraction is reported separately. Clock-boundary brackets are never "
            "treated as stationary roots."
        ),
        "roots": roots,
        "orbit_seeds": [
            {
                "knot_id": knot_id,
                "station": r["station"],
                "angle_index": r["angle_index"],
                "rho_over_rc": r["rho_over_rc"],
                "position_over_rc": r["position_over_rc"],
                "directions": [r["azimuthal_seed_direction"], (-np.asarray(r["azimuthal_seed_direction"])).tolist()],
                "seed_only": True,
                "global_closed_orbit_certified": False,
            }
            for r in min_roots
        ],
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
        "guard": (
            "A converged radial stationary minimum in a sampled normal plane is not yet a closed "
            "Fermat geodesic in the full non-axisymmetric metric."
        ),
    }


def _roots_by_ray(result: dict[str, Any], classifications: set[str] | None = None) -> dict[tuple[int, int], list[dict[str, Any]]]:
    out: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for root in result["roots"]:
        if classifications and root["classification"] not in classifications:
            continue
        key = (int(root["station"]), int(root["angle_index"]))
        out.setdefault(key, []).append(root)
    for rows in out.values():
        rows.sort(key=lambda r: r["rho_over_rc"])
    return out


def certify_candidate_convergence(
    knot_id: str,
    *,
    epsilon: float,
    point_counts: Sequence[int],
    scale_over_rc: float = 1.0,
    stations: int = 8,
    angles: int = 16,
    rho_min: float = 5e-4,
    rho_max: float = 0.03,
    bracket_samples: int = 96,
    relative_tolerance: float = 1e-3,
    strong_relative_tolerance: float = 1e-4,
    force_python: bool = False,
    auto_build: bool = True,
    reach_pair_points: int = 2048,
) -> dict[str, Any]:
    counts = sorted(set(int(v) for v in point_counts))
    if len(counts) < 3 or counts[0] < 16:
        raise ValueError("point_counts must contain at least three values >=16")
    levels: dict[int, dict[str, Any]] = {}
    for i, n in enumerate(counts):
        levels[n] = scan_stationary_candidates(
            knot_id,
            epsilon=epsilon,
            centerline_points=n,
            scale_over_rc=scale_over_rc,
            stations=stations,
            angles=angles,
            rho_min=rho_min,
            rho_max=rho_max,
            bracket_samples=bracket_samples,
            force_python=force_python,
            auto_build=auto_build if i == 0 else False,
            reach_pair_points=reach_pair_points,
        )
    classifications = {"RESOLVED_LOCAL_MINIMUM", "GLOBAL_CAUSTIC_REGIME"}
    maps = {n: _roots_by_ray(levels[n], classifications) for n in counts}
    high_n = counts[-1]
    high_roots = maps[high_n]
    branches: list[dict[str, Any]] = []
    branch_number = 0
    for ray_key, roots_high in high_roots.items():
        for high_root in roots_high:
            matched: list[tuple[int, dict[str, Any]]] = [(high_n, high_root)]
            target = float(high_root["rho_over_rc"])
            for n in reversed(counts[:-1]):
                options = maps[n].get(ray_key, [])
                if not options:
                    continue
                best = min(options, key=lambda r: abs(float(r["rho_over_rc"]) - target))
                if abs(float(best["rho_over_rc"]) - target) / max(target, 1e-30) <= 0.25:
                    matched.append((n, best))
                    target = float(best["rho_over_rc"])
            matched.sort(key=lambda item: item[0])
            branch_number += 1
            errors: dict[str, float | None] = {"rho_relative": None, "R_F_relative": None, "beta_vector_relative": None}
            if len(matched) >= 2:
                _, prev = matched[-2]
                _, cur = matched[-1]
                errors["rho_relative"] = abs(cur["rho_over_rc"] - prev["rho_over_rc"]) / max(abs(cur["rho_over_rc"]), 1e-30)
                errors["R_F_relative"] = abs(cur["R_F_over_rc"] - prev["R_F_over_rc"]) / max(abs(cur["R_F_over_rc"]), 1e-30)
                bcur = np.asarray(cur["beta_vector"], dtype=float)
                bprev = np.asarray(prev["beta_vector"], dtype=float)
                errors["beta_vector_relative"] = float(np.linalg.norm(bcur - bprev) / max(np.linalg.norm(bcur), 1e-30))
            weak = (
                len(matched) >= 3
                and all(v is not None and v < relative_tolerance for v in errors.values())
                and matched[-1][1]["classification"] == "RESOLVED_LOCAL_MINIMUM"
                and matched[-1][1]["inside_approximate_reach"] is not False
            )
            strong = weak and all(v is not None and v < strong_relative_tolerance for v in errors.values())
            branches.append({
                "branch_id": f"{knot_id}/B{branch_number:04d}",
                "ray": {"station": ray_key[0], "angle_index": ray_key[1]},
                "levels_present": [n for n, _ in matched],
                "roots": [{"centerline_points": n, **root} for n, root in matched],
                "errors_last_two_levels": errors,
                "weakly_certified": weak,
                "strongly_certified": strong,
                "classification": "STRONGLY_CERTIFIED" if strong else ("WEAKLY_CERTIFIED" if weak else "NOT_CONVERGED"),
            })
    return {
        "schema": "sst.fermat.convergence-report.v0.4.3",
        "package_version": PACKAGE_VERSION,
        "status": "RESEARCH_TRACK_CANDIDATE_CERTIFICATION",
        "knot_id": knot_id,
        "epsilon_over_rc": epsilon,
        "point_counts": counts,
        "relative_tolerance": relative_tolerance,
        "strong_relative_tolerance": strong_relative_tolerance,
        "levels": levels,
        "branches": branches,
        "weakly_certified_branch_count": sum(bool(b["weakly_certified"]) for b in branches),
        "strongly_certified_branch_count": sum(bool(b["strongly_certified"]) for b in branches),
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }


def build_bifurcation_atlas(
    knot_ids: Iterable[str] = DEFAULT_KNOT_IDS,
    *,
    epsilon_values: Sequence[float],
    centerline_points: int | dict[str, int],
    scale_over_rc: float = 1.0,
    stations: int = 8,
    angles: int = 16,
    rho_min: float = 5e-4,
    rho_max: float = 0.03,
    bracket_samples: int = 96,
    force_python: bool = False,
    auto_build: bool = True,
    reach_pair_points: int = 1024,
) -> dict[str, Any]:
    ids = validate_knot_ids(knot_ids)
    eps = sorted(set(float(v) for v in epsilon_values))
    if not eps or any(v <= 0 for v in eps):
        raise ValueError("positive epsilon_values required")
    if isinstance(centerline_points, dict):
        point_map = {k: int(centerline_points[k]) for k in ids}
    else:
        point_map = {k: int(centerline_points) for k in ids}
    if any(n < 16 for n in point_map.values()):
        raise ValueError("all centerline point counts must be >=16")
    scans: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    branches: list[dict[str, Any]] = []
    first = True
    for knot_id in ids:
        knot_points = point_map[knot_id]
        knot_scans: dict[str, Any] = {}
        active: dict[tuple[int, int], list[dict[str, Any]]] = {}
        all_branches: list[dict[str, Any]] = []
        branch_counter = 0
        cached_reach: dict[str, Any] | None = None
        for ei, epsilon in enumerate(eps):
            scan = scan_stationary_candidates(
                knot_id,
                epsilon=epsilon,
                centerline_points=knot_points,
                scale_over_rc=scale_over_rc,
                stations=stations,
                angles=angles,
                rho_min=rho_min,
                rho_max=rho_max,
                bracket_samples=bracket_samples,
                force_python=force_python,
                auto_build=auto_build if first else False,
                reach_pair_points=reach_pair_points,
                reach_override=cached_reach,
            )
            first = False
            if cached_reach is None:
                cached_reach = scan["reach_diagnostic"]
            knot_scans[f"{epsilon:.10g}"] = scan
            roots = _roots_by_ray(scan, {"RESOLVED_LOCAL_MINIMUM", "GLOBAL_CAUSTIC_REGIME"})
            seen_branch_ids: set[str] = set()
            for ray_key, ray_roots in roots.items():
                existing = active.setdefault(ray_key, [])
                used: set[int] = set()
                for root in ray_roots:
                    best_i = None
                    best_rel = math.inf
                    for i, branch in enumerate(existing):
                        if i in used:
                            continue
                        previous_rho = float(branch["points"][-1]["rho_over_rc"])
                        rel = abs(float(root["rho_over_rc"]) - previous_rho) / max(abs(previous_rho), 1e-30)
                        if rel < best_rel:
                            best_rel, best_i = rel, i
                    if best_i is None or best_rel > 0.30 or existing[best_i]["epsilon_index_last"] != ei - 1:
                        branch_counter += 1
                        branch = {
                            "branch_id": f"{knot_id}/B{branch_counter:04d}",
                            "knot_id": knot_id,
                            "ray": {"station": ray_key[0], "angle_index": ray_key[1]},
                            "points": [],
                            "epsilon_index_last": ei,
                        }
                        existing.append(branch)
                        all_branches.append(branch)
                        best_i = len(existing) - 1
                    branch = existing[best_i]
                    branch["points"].append({"epsilon_over_rc": epsilon, **root})
                    branch["epsilon_index_last"] = ei
                    used.add(best_i)
                    seen_branch_ids.add(branch["branch_id"])
            rows.append({
                "knot_id": knot_id,
                "epsilon_over_rc": epsilon,
                "local_minimum_count": scan["local_minimum_count"],
                "rays_with_local_minimum_count": scan["rays_with_local_minimum_count"],
                "candidate_surface_fraction": scan["candidate_surface_fraction"],
                "candidate_surface_fraction_all_rays": scan["candidate_surface_fraction_all_rays"],
                "candidate_surface_fraction_fully_clock_valid_rays": scan["candidate_surface_fraction_fully_clock_valid_rays"],
                "valid_clock_ray_count": scan["valid_clock_ray_count"],
                "fully_clock_valid_ray_count": scan["fully_clock_valid_ray_count"],
                "rays_with_disconnected_clock_domain": scan["rays_with_disconnected_clock_domain"],
                "clock_boundary_bracket_count": scan["clock_boundary_bracket_count"],
                "invalid_clock_probe_count": scan["invalid_clock_probe_count"],
                "centerline_points": knot_points,
                "scale_over_rc": scale_over_rc,
            })
        for branch in all_branches:
            points = branch["points"]
            first_present = float(points[0]["epsilon_over_rc"])
            last_present = float(points[-1]["epsilon_over_rc"])
            first_index = eps.index(first_present)
            last_index = eps.index(last_present)
            branch["epsilon_first_present_sample"] = first_present
            branch["epsilon_last_present_sample"] = last_present
            branch["onset_left_censored"] = first_index == 0
            branch["loss_right_censored"] = last_index == len(eps) - 1
            branch["epsilon_onset_bracket_over_rc"] = (
                None if first_index == 0 else [float(eps[first_index - 1]), first_present]
            )
            branch["epsilon_loss_bracket_over_rc"] = (
                None if last_index == len(eps) - 1 else [last_present, float(eps[last_index + 1])]
            )
            branch["observed_epsilon_count"] = len(points)
            branch.pop("epsilon_index_last", None)
        scans[knot_id] = knot_scans
        branches.extend(all_branches)
    threshold = constants.ROSENHEAD_CRITICAL_THRESHOLD
    summaries: list[dict[str, Any]] = []
    for knot_id in ids:
        knot_branches = [b for b in branches if b["knot_id"] == knot_id]
        knot_rows = [r for r in rows if r["knot_id"] == knot_id]
        presence = [int(r["rays_with_local_minimum_count"]) > 0 for r in knot_rows]
        present_indices = [i for i, flag in enumerate(presence) if flag]
        if present_indices:
            first_i = present_indices[0]
            last_i = present_indices[-1]
            first_present = float(eps[first_i])
            last_present = float(eps[last_i])
            onset_left_censored = first_i == 0
            loss_right_censored = last_i == len(eps) - 1
            onset_bracket = None if onset_left_censored else [float(eps[first_i - 1]), first_present]
            loss_bracket = None if loss_right_censored else [last_present, float(eps[last_i + 1])]
            loss_midpoint = (0.5 * (loss_bracket[0] + loss_bracket[1])) if loss_bracket else None
        else:
            first_present = last_present = None
            onset_left_censored = loss_right_censored = False
            onset_bracket = loss_bracket = None
            loss_midpoint = None
        summaries.append({
            "knot_id": knot_id,
            "branch_count": len(knot_branches),
            "epsilon_first_present_sample": first_present,
            "epsilon_last_present_sample": last_present,
            "onset_left_censored": onset_left_censored,
            "loss_right_censored": loss_right_censored,
            "epsilon_onset_bracket_over_rc": onset_bracket,
            "epsilon_loss_bracket_over_rc": loss_bracket,
            "sampled_loss_bracket_midpoint_over_rc": loss_midpoint,
            "sampled_loss_bracket_midpoint_shift_from_straight": (
                loss_midpoint - threshold if loss_midpoint is not None else None
            ),
            "threshold_classification": (
                "BRACKETED_SAMPLED_THRESHOLD_NOT_CONTINUATION_CERTIFIED"
                if loss_bracket is not None else
                "RIGHT_CENSORED_NO_SAMPLED_LOSS"
                if loss_right_censored else
                "NO_BRANCH_PRESENT_IN_SCAN"
            ),
        })
    return {
        "schema": "sst.fermat.bifurcation-atlas.v0.4.3",
        "package_version": PACKAGE_VERSION,
        "status": "RESEARCH_TRACK_BIFURCATION_DIAGNOSTIC",
        "knot_ids": list(ids),
        "epsilon_values_over_rc": eps,
        "settings": {
            "centerline_points_by_knot": point_map,
            "scale_over_rc": scale_over_rc,
            "stations": stations,
            "angles": angles,
            "rho_min_over_rc": rho_min,
            "rho_max_over_rc": rho_max,
            "bracket_samples": bracket_samples,
        },
        "straight_reference_critical_threshold": threshold,
        "rows": rows,
        "branch_summaries": summaries,
        "branches": branches,
        "scans": scans,
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }


def symmetry_field_audit(
    knot_id: str,
    *,
    epsilon: float,
    centerline_points: int = 2048,
    scale_over_rc: float = 1.0,
    stations: int = 2,
    angles: int = 4,
    rho_values: Sequence[float] = (0.0015, 0.0020, 0.0030),
    force_python: bool = False,
    auto_build: bool = True,
) -> dict[str, Any]:
    curve = sample_ideal_knot(knot_id, centerline_points, scale_over_rc=scale_over_rc)
    rays, _ = build_rays(curve, stations=stations, angles=angles)
    rhos = np.asarray(list(rho_values), dtype=float)
    points = np.asarray([r.origin + rho * r.radial_direction for r in rays for rho in rhos])
    dirs = np.asarray([r.radial_direction for r in rays for _ in rhos])
    tiled = np.tile(rhos, len(rays))
    base, backend = _evaluate_points(
        curve, points, dirs, tiled,
        epsilon=epsilon, kernel_model="rosenhead_midpoint",
        force_python=force_python, auto_build=auto_build,
    )
    transforms: list[dict[str, Any]] = []

    def audit(name: str, c2: np.ndarray, p2: np.ndarray, d2: np.ndarray, axial: np.ndarray, spatial: np.ndarray):
        q, _ = _evaluate_points(
            c2, p2, d2, tiled,
            epsilon=epsilon, kernel_model="rosenhead_midpoint",
            force_python=force_python, auto_build=False,
        )
        expected_beta = base["beta"] @ axial.T
        expected_j = np.einsum("ab,nbc,dc->nad", axial, base["jacobian"], spatial)
        transforms.append({
            "name": name,
            "beta_vector_linf_error": float(np.max(np.abs(q["beta"] - expected_beta))),
            "beta_magnitude_linf_error": float(np.max(np.abs(np.linalg.norm(q["beta"], axis=1) - np.linalg.norm(base["beta"], axis=1)))),
            "jacobian_linf_error": float(np.max(np.abs(q["jacobian"] - expected_j))),
            "G_linf_error": float(np.max(np.abs(q["G"] - base["G"]))),
        })

    eye = np.eye(3)
    shift = np.asarray([0.37, -0.21, 0.13])
    audit("translation", curve + shift, points + shift, dirs, eye, eye)
    angle = 0.713
    axis = np.asarray([1.0, 2.0, -1.0]); axis /= np.linalg.norm(axis)
    kx = np.asarray([[0.0,-axis[2],axis[1]],[axis[2],0.0,-axis[0]],[-axis[1],axis[0],0.0]])
    rot = eye * math.cos(angle) + (1-math.cos(angle))*np.outer(axis,axis) + math.sin(angle)*kx
    audit("proper_rotation", curve @ rot.T, points @ rot.T, dirs @ rot.T, rot, rot)
    # Reversing the oriented centerline flips the field and Jacobian signs.
    audit("orientation_reversal", curve[::-1].copy(), points, dirs, -eye, eye)
    audit("cyclic_reindex", np.roll(curve, 137 % len(curve), axis=0), points, dirs, eye, eye)
    mirror = np.diag([-1.0, 1.0, 1.0])
    axial = np.linalg.det(mirror) * mirror
    audit("mirror_pseudovector", curve @ mirror.T, points @ mirror.T, dirs @ mirror.T, axial, mirror)
    return {
        "schema": "sst.fermat.symmetry-audit.v0.4.3",
        "package_version": PACKAGE_VERSION,
        "knot_id": knot_id,
        "epsilon_over_rc": epsilon,
        "backend": backend,
        "transform_results": transforms,
        "max_beta_vector_linf_error": max(t["beta_vector_linf_error"] for t in transforms),
        "max_jacobian_linf_error": max(t["jacobian_linf_error"] for t in transforms),
        "max_scalar_G_linf_error": max(t["G_linf_error"] for t in transforms),
        "physical_twist_certified": False,
        "global_closed_orbit_certified": False,
    }
