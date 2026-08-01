from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

import numpy as np

from . import constants
from .core import PACKAGE_VERSION, backend_biot_savart_field_jacobian
from .knot_catalog import (
    DEFAULT_KNOT_IDS,
    centerline_summary,
    knot_metadata,
    sample_ideal_knot,
    validate_knot_ids,
)
from .knot_scan import parallel_transport_frames, rosenhead_reference_regime
from .resolution import resolution_plan


CLOCK_EPS = 1e-15
DEFAULT_ROOT_ABS_TOL = 1e-11
DEFAULT_ROOT_REL_TOL = 1e-9


@dataclass(frozen=True)
class RayGeometry:
    ray_index: int
    station: int
    centerline_index: int
    station_fraction: float
    angle_index: int
    theta_rad: float
    origin: np.ndarray
    tangent: np.ndarray
    radial_direction: np.ndarray
    azimuthal_seed_direction: np.ndarray


def _unit(vector: np.ndarray) -> np.ndarray:
    vector = np.asarray(vector, dtype=float)
    norm = float(np.linalg.norm(vector))
    if not math.isfinite(norm) or norm <= 1e-15:
        raise ValueError("degenerate vector")
    return vector / norm


def _query_field_jacobian(
    curve: np.ndarray,
    probes: np.ndarray,
    *,
    epsilon: float,
    force_python: bool,
    auto_build: bool,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    raw, backend = backend_biot_savart_field_jacobian(
        np.asarray(curve, dtype=float).tolist(),
        np.asarray(probes, dtype=float).tolist(),
        epsilon=epsilon,
        force_python=force_python,
        auto_build=auto_build,
    )
    beta = np.asarray(raw["beta"], dtype=float)
    jacobian = np.asarray(raw["jacobian"], dtype=float)
    if beta.shape != (len(probes), 3):
        raise RuntimeError(f"unexpected beta shape {beta.shape}")
    if jacobian.shape != (len(probes), 3, 3):
        raise RuntimeError(f"unexpected Jacobian shape {jacobian.shape}")
    return beta, jacobian, backend


def _stationary_quantities(
    beta: np.ndarray,
    jacobian: np.ndarray,
    radial_directions: np.ndarray,
    rhos: np.ndarray,
) -> dict[str, np.ndarray]:
    """Evaluate the radial Fermat stationary equation with strict clock-domain gating.

    The polynomial-like numerator

        G = S^2 + rho beta . (J e_rho)

    has the same zero set as d(rho/S)/d rho inside the real clock domain.  No
    fractional power is evaluated until ``S^2 > 0`` has been established.  This
    is the v0.4.2 fix for the v0.4.1 complex-number failure below the horizon gate.
    """
    beta = np.asarray(beta, dtype=float)
    jacobian = np.asarray(jacobian, dtype=float)
    directions = np.asarray(radial_directions, dtype=float)
    rhos = np.asarray(rhos, dtype=float)
    beta2 = np.einsum("ij,ij->i", beta, beta)
    s2 = 1.0 - beta2
    valid = np.isfinite(s2) & (s2 > CLOCK_EPS)
    beta_prime = np.einsum("nij,nj->ni", jacobian, directions)
    beta_dot_prime = np.einsum("ij,ij->i", beta, beta_prime)
    g = np.full(len(beta), np.nan, dtype=float)
    g[valid] = s2[valid] + rhos[valid] * beta_dot_prime[valid]
    d_rf = np.full(len(beta), np.nan, dtype=float)
    # Safe because the mask is applied before the fractional power.
    d_rf[valid] = g[valid] / np.power(s2[valid], 1.5)
    s = np.full(len(beta), np.nan, dtype=float)
    s[valid] = np.sqrt(s2[valid])
    rf = np.full(len(beta), np.nan, dtype=float)
    rf[valid] = rhos[valid] / s[valid]
    return {
        "beta2": beta2,
        "s2": s2,
        "clock_valid": valid,
        "beta_prime": beta_prime,
        "beta_dot_prime": beta_dot_prime,
        "G": g,
        "d_R_F": d_rf,
        "S": s,
        "R_F": rf,
    }


def _build_rays(
    curve: np.ndarray,
    *,
    stations: int,
    angles: int,
) -> tuple[list[RayGeometry], dict[str, Any]]:
    if stations < 1 or angles < 3:
        raise ValueError("stations>=1 and angles>=3 required")
    curve = np.asarray(curve, dtype=float)
    tangents, n1, n2, mismatch = parallel_transport_frames(curve)
    station_indices = np.floor(np.arange(stations) * len(curve) / stations).astype(int)
    rays: list[RayGeometry] = []
    for station, index_raw in enumerate(station_indices):
        index = int(index_raw)
        tangent = _unit(tangents[index])
        for angle_index in range(angles):
            theta = 2.0 * math.pi * angle_index / angles
            radial = _unit(math.cos(theta) * n1[index] + math.sin(theta) * n2[index])
            azimuthal = _unit(np.cross(tangent, radial))
            rays.append(
                RayGeometry(
                    ray_index=len(rays),
                    station=station,
                    centerline_index=index,
                    station_fraction=station / stations,
                    angle_index=angle_index,
                    theta_rad=theta,
                    origin=curve[index].copy(),
                    tangent=tangent.copy(),
                    radial_direction=radial,
                    azimuthal_seed_direction=azimuthal,
                )
            )
    return rays, {
        "method": "discrete_Bishop_parallel_transport",
        "closure_mismatch_rad": float(mismatch),
        "station_indices": station_indices.tolist(),
        "physical_twist_certified": False,
        "tangent_count": int(len(tangents)),
    }


def _probe_grid(
    rays: Sequence[RayGeometry],
    *,
    rho_min: float,
    rho_max: float,
    bracket_samples: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if not (0.0 < rho_min < rho_max):
        raise ValueError("require 0 < rho_min < rho_max")
    if bracket_samples < 16:
        raise ValueError("bracket_samples>=16 required")
    rhos_single = np.geomspace(rho_min, rho_max, bracket_samples)
    probes = np.empty((len(rays) * bracket_samples, 3), dtype=float)
    directions = np.empty_like(probes)
    rhos = np.tile(rhos_single, len(rays))
    ray_ids = np.repeat(np.arange(len(rays), dtype=int), bracket_samples)
    cursor = 0
    for ray in rays:
        sl = slice(cursor, cursor + bracket_samples)
        probes[sl] = ray.origin[None, :] + rhos_single[:, None] * ray.radial_direction[None, :]
        directions[sl] = ray.radial_direction
        cursor += bracket_samples
    return probes, directions, rhos, ray_ids


def approximate_reach_diagnostic(
    curve: np.ndarray,
    *,
    pair_points: int = 1024,
    local_index_exclusion: int = 8,
    tangent_perpendicular_tolerance: float = 0.08,
) -> dict[str, Any]:
    """Return a deliberately non-rigorous reach diagnostic.

    Candidate non-local chords must be approximately perpendicular to both
    endpoint tangents.  This avoids mistaking a merely nearby point along the
    same smooth arc for a doubly-critical self-distance.
    """
    curve = np.asarray(curve, dtype=float)
    n = len(curve)
    if n < 16:
        raise ValueError("curve needs at least 16 points")

    prev = np.roll(curve, 1, axis=0)
    nxt = np.roll(curve, -1, axis=0)
    a = np.linalg.norm(curve - prev, axis=1)
    b = np.linalg.norm(nxt - curve, axis=1)
    c = np.linalg.norm(nxt - prev, axis=1)
    twice_area = np.linalg.norm(np.cross(curve - prev, nxt - curve), axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        curvature_radius = a * b * c / np.maximum(2.0 * twice_area, 1e-300)
    curvature_radius[~np.isfinite(curvature_radius)] = math.inf
    min_curvature = float(np.min(curvature_radius))

    m = min(max(32, pair_points), n)
    indices = np.floor(np.arange(m) * n / m).astype(int)
    points = curve[indices]
    tangents = np.roll(points, -1, axis=0) - np.roll(points, 1, axis=0)
    tangents /= np.maximum(np.linalg.norm(tangents, axis=1)[:, None], 1e-300)
    best_distance = math.inf
    best_pair: tuple[int, int] | None = None
    best_residuals: tuple[float, float] | None = None
    exclusion = max(2, int(math.ceil(local_index_exclusion * m / n)))
    block = 192
    all_j = np.arange(m)
    for i0 in range(0, m, block):
        i1 = min(m, i0 + block)
        delta = points[None, :, :] - points[i0:i1, None, :]
        dist = np.linalg.norm(delta, axis=2)
        chord_unit = delta / np.maximum(dist[:, :, None], 1e-300)
        residual_i = np.abs(np.einsum("bjk,bk->bj", chord_unit, tangents[i0:i1]))
        residual_j = np.abs(np.einsum("bjk,jk->bj", chord_unit, tangents))
        allowed = (residual_i <= tangent_perpendicular_tolerance) & (residual_j <= tangent_perpendicular_tolerance)
        for local_i, global_i in enumerate(range(i0, i1)):
            cyclic = np.minimum((all_j - global_i) % m, (global_i - all_j) % m)
            allowed[local_i, cyclic <= exclusion] = False
        masked = np.where(allowed, dist, math.inf)
        flat = int(np.argmin(masked))
        value = float(masked.flat[flat])
        if value < best_distance:
            li, j = np.unravel_index(flat, masked.shape)
            i = i0 + int(li)
            best_distance = value
            best_pair = (int(indices[i]), int(indices[j]))
            best_residuals = (float(residual_i[li, j]), float(residual_j[li, j]))

    if not math.isfinite(best_distance):
        half_chord = math.inf
        reach = min_curvature
        controlling = "curvature_no_coarse_dcsd_candidate"
    else:
        half_chord = 0.5 * best_distance
        reach = min(min_curvature, half_chord)
        controlling = "curvature" if min_curvature <= half_chord else "coarse_approximate_dcsd"
    return {
        "method": "discrete_curvature_plus_coarse_approximate_dcsd",
        "rigorous_certificate": False,
        "curve_points": int(n),
        "pair_search_points": int(m),
        "local_index_exclusion": int(local_index_exclusion),
        "tangent_perpendicular_tolerance": tangent_perpendicular_tolerance,
        "min_curvature_radius_over_rc": min_curvature,
        "approximate_dcsd_over_rc": best_distance if math.isfinite(best_distance) else None,
        "half_approximate_dcsd_over_rc": half_chord if math.isfinite(half_chord) else None,
        "reach_estimate_over_rc": reach,
        "controlling_term": controlling,
        "dcsd_centerline_index_pair": list(best_pair) if best_pair else None,
        "dcsd_perpendicularity_residuals": list(best_residuals) if best_residuals else None,
        "guard": "Diagnostic only: the coarse perpendicular-chord search is not a certified dcsd computation.",
    }


def _discover_brackets(
    rays: Sequence[RayGeometry],
    rhos_single: np.ndarray,
    q: dict[str, np.ndarray],
    *,
    bracket_samples: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    brackets: list[dict[str, Any]] = []
    clock_boundaries: list[dict[str, Any]] = []
    stats = {
        "fully_clock_valid_ray_count": 0,
        "valid_clock_ray_count": 0,
        "invalid_clock_probe_count": int(np.count_nonzero(~q["clock_valid"])),
    }
    for ray in rays:
        start = ray.ray_index * bracket_samples
        stop = start + bracket_samples
        valid = q["clock_valid"][start:stop]
        g = q["G"][start:stop]
        if bool(np.all(valid)):
            stats["fully_clock_valid_ray_count"] += 1
        if bool(np.any(valid)):
            stats["valid_clock_ray_count"] += 1
        for i in range(bracket_samples - 1):
            if valid[i] != valid[i + 1]:
                clock_boundaries.append({
                    "ray_index": ray.ray_index,
                    "station": ray.station,
                    "angle_index": ray.angle_index,
                    "rho_lo_over_rc": float(rhos_single[i]),
                    "rho_hi_over_rc": float(rhos_single[i + 1]),
                    "classification": "CLOCK_BOUNDARY_BRACKET",
                })
                continue
            if not (valid[i] and valid[i + 1]):
                continue
            gi = float(g[i])
            gj = float(g[i + 1])
            if not (math.isfinite(gi) and math.isfinite(gj)):
                continue
            if gi == 0.0 or gj == 0.0 or gi * gj < 0.0:
                brackets.append({
                    "ray_index": ray.ray_index,
                    "rho_lo": float(rhos_single[i]),
                    "rho_hi": float(rhos_single[i + 1]),
                    "g_lo": gi,
                    "g_hi": gj,
                })
    return brackets, clock_boundaries, stats


def _refine_brackets_batch(
    curve: np.ndarray,
    rays: Sequence[RayGeometry],
    brackets: Sequence[dict[str, Any]],
    *,
    epsilon: float,
    force_python: bool,
    auto_build: bool,
    abs_tol: float,
    rel_tol: float,
    max_iterations: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    if not brackets:
        return [], {"backend": "python" if force_python else "unknown", "build": None, "import_error": None}, []
    lo = np.asarray([b["rho_lo"] for b in brackets], dtype=float)
    hi = np.asarray([b["rho_hi"] for b in brackets], dtype=float)
    g_lo = np.asarray([b["g_lo"] for b in brackets], dtype=float)
    g_hi = np.asarray([b["g_hi"] for b in brackets], dtype=float)
    ray_indices = np.asarray([b["ray_index"] for b in brackets], dtype=int)
    active = np.ones(len(brackets), dtype=bool)
    invalid_splits: list[dict[str, Any]] = []
    backend: dict[str, Any] | None = None

    for iteration in range(max_iterations):
        indices = np.flatnonzero(active)
        if not len(indices):
            break
        widths = hi[indices] - lo[indices]
        tolerance = abs_tol + rel_tol * np.maximum(np.abs(lo[indices]), np.abs(hi[indices]))
        converged = widths <= tolerance
        if np.any(converged):
            active[indices[converged]] = False
            indices = indices[~converged]
        if not len(indices):
            break
        mid = 0.5 * (lo[indices] + hi[indices])
        probes = np.vstack([
            rays[int(ray_indices[idx])].origin + mid_i * rays[int(ray_indices[idx])].radial_direction
            for idx, mid_i in zip(indices, mid)
        ])
        directions = np.vstack([rays[int(ray_indices[idx])].radial_direction for idx in indices])
        beta, jac, backend_now = _query_field_jacobian(
            curve, probes, epsilon=epsilon, force_python=force_python,
            auto_build=auto_build if backend is None else False,
        )
        backend = backend_now
        q = _stationary_quantities(beta, jac, directions, mid)
        for local, index in enumerate(indices):
            if not bool(q["clock_valid"][local]) or not math.isfinite(float(q["G"][local])):
                ray = rays[int(ray_indices[index])]
                invalid_splits.append({
                    "ray_index": ray.ray_index,
                    "station": ray.station,
                    "angle_index": ray.angle_index,
                    "rho_lo_over_rc": float(lo[index]),
                    "rho_hi_over_rc": float(hi[index]),
                    "rho_mid_over_rc": float(mid[local]),
                    "classification": "CLOCK_DOMAIN_SPLIT_DURING_REFINEMENT",
                })
                active[index] = False
                lo[index] = hi[index] = math.nan
                continue
            gm = float(q["G"][local])
            if g_lo[index] == 0.0:
                hi[index] = lo[index]
                g_hi[index] = g_lo[index]
                active[index] = False
            elif g_hi[index] == 0.0:
                lo[index] = hi[index]
                g_lo[index] = g_hi[index]
                active[index] = False
            elif g_lo[index] * gm <= 0.0:
                hi[index] = mid[local]
                g_hi[index] = gm
            else:
                lo[index] = mid[local]
                g_lo[index] = gm
    else:
        # Any remaining active bracket is returned but marked by width; callers can reject it.
        pass

    refined: list[dict[str, Any]] = []
    for index, bracket in enumerate(brackets):
        if not (math.isfinite(float(lo[index])) and math.isfinite(float(hi[index]))):
            continue
        refined.append({
            **bracket,
            "rho_lo": float(lo[index]),
            "rho_hi": float(hi[index]),
            "g_lo": float(g_lo[index]),
            "g_hi": float(g_hi[index]),
            "rho_root": float(0.5 * (lo[index] + hi[index])),
            "bracket_width": float(hi[index] - lo[index]),
        })
    if backend is None:
        backend = {"backend": "python" if force_python else "unknown", "build": None, "import_error": None}
    return refined, backend, invalid_splits


def _root_records(
    curve: np.ndarray,
    rays: Sequence[RayGeometry],
    refined: Sequence[dict[str, Any]],
    *,
    epsilon: float,
    force_python: bool,
    auto_build: bool,
    reach_estimate: float | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not refined:
        return [], {"backend": "python" if force_python else "unknown", "build": None, "import_error": None}
    rhos = np.asarray([b["rho_root"] for b in refined], dtype=float)
    ray_indices = np.asarray([b["ray_index"] for b in refined], dtype=int)
    probes = np.vstack([
        rays[int(ray_i)].origin + rho * rays[int(ray_i)].radial_direction
        for ray_i, rho in zip(ray_indices, rhos)
    ])
    directions = np.vstack([rays[int(ray_i)].radial_direction for ray_i in ray_indices])
    beta, jac, backend = _query_field_jacobian(
        curve, probes, epsilon=epsilon, force_python=force_python, auto_build=auto_build
    )
    q = _stationary_quantities(beta, jac, directions, rhos)
    roots: list[dict[str, Any]] = []
    for i, bracket in enumerate(refined):
        ray = rays[int(ray_indices[i])]
        if not bool(q["clock_valid"][i]):
            continue
        s = float(q["S"][i])
        bvec = beta[i]
        jmat = jac[i]
        grad_s = -(jmat.T @ bvec) / s
        # Classification uses G endpoint ordering, which has the same sign as dR/drho.
        if bracket["g_lo"] < 0.0 < bracket["g_hi"]:
            classification = "RESOLVED_LOCAL_MINIMUM"
        elif bracket["g_lo"] > 0.0 > bracket["g_hi"]:
            classification = "LOCAL_MAXIMUM"
        else:
            classification = "DEGENERATE_OR_ENDPOINT_STATIONARY_POINT"
        width = max(float(bracket["bracket_width"]), 1e-300)
        # Near a simple root, dR/drho = G/S^3; use endpoint G slope and root S.
        second_estimate = (float(bracket["g_hi"]) - float(bracket["g_lo"])) / (width * s**3)
        rho = float(rhos[i])
        roots.append({
            "ray_index": ray.ray_index,
            "station": ray.station,
            "centerline_index": ray.centerline_index,
            "station_fraction": ray.station_fraction,
            "angle_index": ray.angle_index,
            "theta_rad": ray.theta_rad,
            "rho_over_rc": rho,
            "r_m": rho * constants.R_C,
            "position_over_rc": probes[i].tolist(),
            "radial_direction": ray.radial_direction.tolist(),
            "azimuthal_seed_direction": ray.azimuthal_seed_direction.tolist(),
            "beta_vector": bvec.tolist(),
            "beta_magnitude": float(np.linalg.norm(bvec)),
            "jacobian": jmat.tolist(),
            "grad_S": grad_s.tolist(),
            "S": s,
            "R_F_over_rc": float(q["R_F"][i]),
            "stationary_residual_G": float(q["G"][i]),
            "bracket_width_over_rc": float(bracket["bracket_width"]),
            "R_F_second_estimate": float(second_estimate),
            "clock_valid": True,
            "classification": classification,
            "global_closed_orbit_certified": False,
            "inside_approximate_reach": (
                None if reach_estimate is None else rho < reach_estimate
            ),
        })
    roots.sort(key=lambda r: (r["station"], r["angle_index"], r["rho_over_rc"]))
    return roots, backend


def scan_stationary_candidates(
    knot_id: str,
    *,
    epsilon: float = 0.0019,
    centerline_points: int = 8192,
    scale_over_rc: float = 1.0,
    stations: int = 8,
    angles: int = 16,
    rho_min: float = 0.0005,
    rho_max: float = 0.03,
    bracket_samples: int = 96,
    root_abs_tol: float = DEFAULT_ROOT_ABS_TOL,
    root_rel_tol: float = DEFAULT_ROOT_REL_TOL,
    max_root_iterations: int = 80,
    reach_pair_points: int = 1024,
    force_python: bool = False,
    auto_build: bool = True,
    reach_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validate_knot_ids([knot_id])
    if epsilon <= 0.0:
        raise ValueError("epsilon must be positive")
    curve = sample_ideal_knot(knot_id, centerline_points, scale_over_rc=scale_over_rc)
    rays, frame = _build_rays(curve, stations=stations, angles=angles)
    probes, directions, rhos, _ = _probe_grid(
        rays, rho_min=rho_min, rho_max=rho_max, bracket_samples=bracket_samples
    )
    beta, jac, discovery_backend = _query_field_jacobian(
        curve, probes, epsilon=epsilon, force_python=force_python, auto_build=auto_build
    )
    q = _stationary_quantities(beta, jac, directions, rhos)
    rhos_single = np.geomspace(rho_min, rho_max, bracket_samples)
    brackets, clock_boundaries, clock_stats = _discover_brackets(
        rays, rhos_single, q, bracket_samples=bracket_samples
    )
    refined, refine_backend, invalid_splits = _refine_brackets_batch(
        curve, rays, brackets,
        epsilon=epsilon,
        force_python=force_python,
        auto_build=False,
        abs_tol=root_abs_tol,
        rel_tol=root_rel_tol,
        max_iterations=max_root_iterations,
    )
    reach = reach_override or approximate_reach_diagnostic(
        curve, pair_points=reach_pair_points
    )
    roots, root_backend = _root_records(
        curve, rays, refined,
        epsilon=epsilon,
        force_python=force_python,
        auto_build=False,
        reach_estimate=reach.get("reach_estimate_over_rc"),
    )
    minima = [r for r in roots if r["classification"] == "RESOLVED_LOCAL_MINIMUM"]
    rays_with_min = {(r["station"], r["angle_index"]) for r in minima}
    fully_valid_rays = set()
    for ray in rays:
        start = ray.ray_index * bracket_samples
        if bool(np.all(q["clock_valid"][start:start + bracket_samples])):
            fully_valid_rays.add((ray.station, ray.angle_index))
    rays_with_min_fully = rays_with_min & fully_valid_rays
    ray_count = len(rays)
    valid_ray_count = int(clock_stats["valid_clock_ray_count"])
    fully_valid_count = int(clock_stats["fully_clock_valid_ray_count"])
    orbit_seeds = [{
        "knot_id": knot_id,
        "station": r["station"],
        "angle_index": r["angle_index"],
        "rho_over_rc": r["rho_over_rc"],
        "position_over_rc": r["position_over_rc"],
        "directions": [r["azimuthal_seed_direction"], [-x for x in r["azimuthal_seed_direction"]]],
        "seed_only": True,
        "global_closed_orbit_certified": False,
    } for r in minima]
    backend = root_backend if root_backend.get("backend") != "unknown" else (
        refine_backend if refine_backend.get("backend") != "unknown" else discovery_backend
    )
    return {
        "schema": "sst.fermat.candidate-atlas.v0.4.2",
        "package_version": PACKAGE_VERSION,
        "status": "RESEARCH_TRACK_STATIONARY_ROOT_RESOLUTION",
        "knot_id": knot_id,
        "source": knot_metadata(knot_id),
        "backend": backend,
        "settings": {
            "epsilon_over_rc": epsilon,
            "kernel_model": "rosenhead_midpoint",
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
        "ray_count": ray_count,
        "fully_clock_valid_ray_count": fully_valid_count,
        "valid_clock_ray_count": valid_ray_count,
        "invalid_clock_probe_count": int(clock_stats["invalid_clock_probe_count"]),
        "clock_boundary_bracket_count": len(clock_boundaries),
        "clock_boundary_brackets": clock_boundaries,
        "clock_domain_split_count": len(invalid_splits),
        "clock_domain_splits": invalid_splits,
        "bracket_count": len(brackets),
        "stationary_root_count": len(roots),
        "local_minimum_count": len(minima),
        "rays_with_local_minimum_count": len(rays_with_min),
        "rays_with_local_minimum_and_fully_clock_valid_count": len(rays_with_min_fully),
        "candidate_surface_fraction": len(rays_with_min) / max(valid_ray_count, 1),
        "candidate_surface_fraction_all_rays": len(rays_with_min) / max(ray_count, 1),
        "candidate_surface_fraction_fully_clock_valid_rays": (
            len(rays_with_min_fully) / fully_valid_count if fully_valid_count else None
        ),
        "candidate_surface_fraction_definition": (
            "candidate_surface_fraction is the fraction of sampled rays with at least one resolved local minimum, "
            "normalized by rays containing at least one real-clock probe. The all-rays and fully-valid variants are "
            "reported separately. Clock-boundary brackets are never treated as stationary roots."
        ),
        "roots": roots,
        "orbit_seeds": orbit_seeds,
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
        "guard": (
            "A resolved or convergence-certified radial stationary minimum in a sampled normal plane is not yet a "
            "closed Fermat geodesic in the full non-axisymmetric metric."
        ),
    }


def build_candidate_atlas(
    knot_ids: Iterable[str] = DEFAULT_KNOT_IDS,
    **kwargs: Any,
) -> dict[str, Any]:
    ids = validate_knot_ids(knot_ids)
    results: dict[str, Any] = {}
    rows: list[dict[str, Any]] = []
    for index, knot_id in enumerate(ids):
        options = dict(kwargs)
        options["auto_build"] = bool(kwargs.get("auto_build", True)) if index == 0 else False
        result = scan_stationary_candidates(knot_id, **options)
        results[knot_id] = result
        rows.append({
            "knot_id": knot_id,
            "backend": result["backend"]["backend"],
            "epsilon_over_rc": result["settings"]["epsilon_over_rc"],
            "centerline_points": result["settings"]["centerline_points"],
            "scale_over_rc": result["settings"]["scale_over_rc"],
            "ray_count": result["ray_count"],
            "local_minimum_count": result["local_minimum_count"],
            "rays_with_local_minimum_count": result["rays_with_local_minimum_count"],
            "candidate_surface_fraction": result["candidate_surface_fraction"],
            "candidate_surface_fraction_all_rays": result["candidate_surface_fraction_all_rays"],
            "candidate_surface_fraction_fully_clock_valid_rays": result[
                "candidate_surface_fraction_fully_clock_valid_rays"
            ],
            "fully_clock_valid_ray_count": result["fully_clock_valid_ray_count"],
            "invalid_clock_probe_count": result["invalid_clock_probe_count"],
            "clock_boundary_bracket_count": result["clock_boundary_bracket_count"],
            "reach_estimate_over_rc": result["reach_diagnostic"]["reach_estimate_over_rc"],
        })
    return {
        "schema": "sst.fermat.candidate-atlas-matrix.v0.4.2",
        "package_version": PACKAGE_VERSION,
        "rows": rows,
        "results": results,
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }


def _relative_error(a: float, b: float, floor: float = 1e-300) -> float:
    return abs(a - b) / max(abs(b), floor)


def certify_candidate_convergence(
    knot_id: str,
    *,
    epsilon: float,
    point_counts: Sequence[int],
    relative_tolerance: float = 1e-3,
    strong_relative_tolerance: float = 1e-4,
    **scan_kwargs: Any,
) -> dict[str, Any]:
    counts = sorted({int(n) for n in point_counts})
    if len(counts) < 3:
        raise ValueError("at least three point counts are required")
    levels: dict[str, Any] = {}
    for index, count in enumerate(counts):
        options = dict(scan_kwargs)
        options["centerline_points"] = count
        options["epsilon"] = epsilon
        options["auto_build"] = bool(scan_kwargs.get("auto_build", True)) if index == 0 else False
        levels[str(count)] = scan_stationary_candidates(knot_id, **options)

    minima_by_level: dict[int, dict[tuple[int, int], dict[str, Any]]] = {}
    for count in counts:
        minima_by_level[count] = {
            (r["station"], r["angle_index"]): r
            for r in levels[str(count)]["roots"]
            if r["classification"] == "RESOLVED_LOCAL_MINIMUM"
        }
    all_rays = sorted(set().union(*(set(m) for m in minima_by_level.values())))
    branches: list[dict[str, Any]] = []
    for branch_number, ray_key in enumerate(all_rays, start=1):
        roots = []
        for count in counts:
            root = minima_by_level[count].get(ray_key)
            if root is not None:
                roots.append({"centerline_points": count, **root})
        errors = None
        weak = False
        strong = False
        if len(roots) >= 3 and roots[-1]["centerline_points"] == counts[-1] and roots[-2]["centerline_points"] == counts[-2]:
            low, high = roots[-2], roots[-1]
            beta_low = np.asarray(low["beta_vector"], dtype=float)
            beta_high = np.asarray(high["beta_vector"], dtype=float)
            errors = {
                "rho_relative": _relative_error(float(low["rho_over_rc"]), float(high["rho_over_rc"])),
                "R_F_relative": _relative_error(float(low["R_F_over_rc"]), float(high["R_F_over_rc"])),
                "beta_vector_relative": float(
                    np.max(np.abs(beta_low - beta_high)) / max(float(np.max(np.abs(beta_high))), 1e-300)
                ),
            }
            weak = max(errors.values()) < relative_tolerance
            strong = max(errors.values()) < strong_relative_tolerance
        classification = "STRONGLY_CERTIFIED" if strong else (
            "WEAKLY_CERTIFIED" if weak else "NOT_CONVERGENCE_CERTIFIED"
        )
        branches.append({
            "branch_id": f"{knot_id}/B{branch_number:04d}",
            "ray": {"station": ray_key[0], "angle_index": ray_key[1]},
            "levels_present": [r["centerline_points"] for r in roots],
            "roots": roots,
            "errors_last_two_levels": errors,
            "weakly_certified": weak,
            "strongly_certified": strong,
            "classification": classification,
        })
    return {
        "schema": "sst.fermat.convergence-report.v0.4.2",
        "package_version": PACKAGE_VERSION,
        "status": "RESEARCH_TRACK_CANDIDATE_CERTIFICATION",
        "knot_id": knot_id,
        "epsilon_over_rc": epsilon,
        "point_counts": counts,
        "relative_tolerance": relative_tolerance,
        "strong_relative_tolerance": strong_relative_tolerance,
        "levels": levels,
        "branches": branches,
        "weakly_certified_branch_count": sum(b["weakly_certified"] for b in branches),
        "strongly_certified_branch_count": sum(b["strongly_certified"] for b in branches),
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }


def build_convergence_matrix(
    knot_ids: Iterable[str],
    *,
    epsilon: float,
    point_counts: Sequence[int],
    **kwargs: Any,
) -> dict[str, Any]:
    ids = validate_knot_ids(knot_ids)
    results: dict[str, Any] = {}
    rows: list[dict[str, Any]] = []
    for index, knot_id in enumerate(ids):
        options = dict(kwargs)
        options["auto_build"] = bool(kwargs.get("auto_build", True)) if index == 0 else False
        result = certify_candidate_convergence(
            knot_id, epsilon=epsilon, point_counts=point_counts, **options
        )
        results[knot_id] = result
        highest = result["levels"][str(max(result["point_counts"]))]
        rows.append({
            "knot_id": knot_id,
            "epsilon_over_rc": epsilon,
            "point_counts": " ".join(map(str, result["point_counts"])),
            "branch_count": len(result["branches"]),
            "weakly_certified_branch_count": result["weakly_certified_branch_count"],
            "strongly_certified_branch_count": result["strongly_certified_branch_count"],
            "highest_backend": highest["backend"]["backend"],
        })
    return {
        "schema": "sst.fermat.convergence-matrix.v0.4.2",
        "package_version": PACKAGE_VERSION,
        "rows": rows,
        "results": results,
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }


def _epsilon_values(start: float, stop: float, step: float) -> list[float]:
    if step <= 0.0 or stop < start:
        raise ValueError("invalid epsilon range")
    n = int(math.floor((stop - start) / step + 0.5))
    values = [start + i * step for i in range(n + 1)]
    if values[-1] < stop - step * 1e-6:
        values.append(stop)
    return [float(round(x, 15)) for x in values]


def build_bifurcation_atlas(
    knot_ids: Iterable[str] = DEFAULT_KNOT_IDS,
    *,
    epsilon_start: float,
    epsilon_stop: float,
    epsilon_step: float,
    resolution_mode: str = "adaptive",
    centerline_points: int = 8192,
    target_ds_over_epsilon: float = 0.5,
    min_centerline_points: int = 32768,
    max_centerline_points: int = 65536,
    round_centerline_points_to: int = 1024,
    **scan_kwargs: Any,
) -> dict[str, Any]:
    ids = validate_knot_ids(knot_ids)
    values = _epsilon_values(epsilon_start, epsilon_stop, epsilon_step)
    rows: list[dict[str, Any]] = []
    results: dict[str, dict[str, Any]] = {k: {} for k in ids}
    cached_reach: dict[tuple[str, int, float], dict[str, Any]] = {}
    first_call = True
    for epsilon in values:
        for knot_id in ids:
            plan = None
            if resolution_mode == "adaptive":
                plan = resolution_plan(
                    knot_id,
                    epsilon=epsilon,
                    scale_over_rc=float(scan_kwargs.get("scale_over_rc", 1.0)),
                    target_ds_over_epsilon=target_ds_over_epsilon,
                    min_points=min_centerline_points,
                    max_points=max_centerline_points,
                    round_to=round_centerline_points_to,
                )
                points = int(plan["selected_points"])
            elif resolution_mode == "fixed":
                points = int(centerline_points)
            else:
                raise ValueError("resolution_mode must be 'adaptive' or 'fixed'")
            reach_key = (knot_id, points, float(scan_kwargs.get("scale_over_rc", 1.0)))
            options = dict(scan_kwargs)
            options.update({
                "epsilon": epsilon,
                "centerline_points": points,
                "auto_build": bool(scan_kwargs.get("auto_build", True)) if first_call else False,
            })
            if reach_key in cached_reach:
                options["reach_override"] = cached_reach[reach_key]
            scan = scan_stationary_candidates(knot_id, **options)
            first_call = False
            cached_reach[reach_key] = scan["reach_diagnostic"]
            results[knot_id][f"{epsilon:.15g}"] = {"resolution_plan": plan, "scan": scan}
            minima = [r for r in scan["roots"] if r["classification"] == "RESOLVED_LOCAL_MINIMUM"]
            rows.append({
                "knot_id": knot_id,
                "epsilon_over_rc": epsilon,
                "centerline_points": points,
                "resolution_mode": resolution_mode,
                "resolution_plan_classification": plan["classification"] if plan else "FIXED",
                "ray_count": scan["ray_count"],
                "local_minimum_count": scan["local_minimum_count"],
                "rays_with_local_minimum_count": scan["rays_with_local_minimum_count"],
                "candidate_surface_fraction_all_rays": scan["candidate_surface_fraction_all_rays"],
                "fully_clock_valid_ray_count": scan["fully_clock_valid_ray_count"],
                "invalid_clock_probe_count": scan["invalid_clock_probe_count"],
                "clock_boundary_bracket_count": scan["clock_boundary_bracket_count"],
                "mean_minimum_rho_over_rc": (
                    float(np.mean([r["rho_over_rc"] for r in minima])) if minima else None
                ),
                "min_minimum_rho_over_rc": (
                    min((r["rho_over_rc"] for r in minima), default=None)
                ),
                "max_minimum_rho_over_rc": (
                    max((r["rho_over_rc"] for r in minima), default=None)
                ),
                "backend": scan["backend"]["backend"],
            })

    thresholds: dict[str, Any] = {}
    for knot_id in ids:
        knot_rows = sorted((r for r in rows if r["knot_id"] == knot_id), key=lambda r: r["epsilon_over_rc"])
        present = [r for r in knot_rows if r["rays_with_local_minimum_count"] > 0]
        thresholds[knot_id] = {
            "epsilon_onset_sampled": min((r["epsilon_over_rc"] for r in present), default=None),
            "epsilon_loss_sampled": max((r["epsilon_over_rc"] for r in present), default=None),
            "straight_reference_critical_threshold": constants.ROSENHEAD_CRITICAL_THRESHOLD,
            "sampled_loss_shift_from_straight": (
                max(r["epsilon_over_rc"] for r in present) - constants.ROSENHEAD_CRITICAL_THRESHOLD
                if present else None
            ),
            "threshold_resolution_over_rc": epsilon_step,
            "classification": "SAMPLED_THRESHOLD_ONLY_NOT_CONTINUATION_CERTIFIED",
        }
    return {
        "schema": "sst.fermat.bifurcation-atlas.v0.4.2",
        "package_version": PACKAGE_VERSION,
        "status": "RESEARCH_TRACK_BIFURCATION_SCAN",
        "settings": {
            "knots": list(ids),
            "epsilon_start": epsilon_start,
            "epsilon_stop": epsilon_stop,
            "epsilon_step": epsilon_step,
            "resolution_mode": resolution_mode,
            "centerline_points": centerline_points,
            "target_ds_over_epsilon": target_ds_over_epsilon,
            "min_centerline_points": min_centerline_points,
            "max_centerline_points": max_centerline_points,
            "round_centerline_points_to": round_centerline_points_to,
        },
        "rows": rows,
        "thresholds": thresholds,
        "results": results,
        "clock_domain_hotfix": {
            "version": "0.4.2",
            "rule": "S^2 <= 0 is classified before any fractional power or S^{-3} evaluation.",
            "clock_boundary_brackets_are_stationary_roots": False,
        },
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }


def build_scale_sweep(
    knot_ids: Iterable[str],
    *,
    scales: Sequence[float],
    epsilon: float,
    resolution_mode: str = "adaptive",
    centerline_points: int = 8192,
    target_ds_over_epsilon: float = 1.0,
    min_centerline_points: int = 4096,
    max_centerline_points: int = 65536,
    round_centerline_points_to: int = 1024,
    **scan_kwargs: Any,
) -> dict[str, Any]:
    ids = validate_knot_ids(knot_ids)
    rows: list[dict[str, Any]] = []
    results: dict[str, Any] = {}
    first = True
    for scale in scales:
        if scale <= 0:
            raise ValueError("scales must be positive")
        for knot_id in ids:
            plan = None
            if resolution_mode == "adaptive":
                plan = resolution_plan(
                    knot_id,
                    epsilon=epsilon,
                    scale_over_rc=float(scale),
                    target_ds_over_epsilon=target_ds_over_epsilon,
                    min_points=min_centerline_points,
                    max_points=max_centerline_points,
                    round_to=round_centerline_points_to,
                )
                points = int(plan["selected_points"])
            else:
                points = int(centerline_points)
            options = dict(scan_kwargs)
            options.update({
                "epsilon": epsilon,
                "centerline_points": points,
                "scale_over_rc": float(scale),
                "auto_build": bool(scan_kwargs.get("auto_build", True)) if first else False,
            })
            scan = scan_stationary_candidates(knot_id, **options)
            first = False
            key = f"{knot_id}@{scale:g}"
            results[key] = {"resolution_plan": plan, "scan": scan}
            minima = [r for r in scan["roots"] if r["classification"] == "RESOLVED_LOCAL_MINIMUM"]
            rows.append({
                "knot_id": knot_id,
                "scale_over_rc": float(scale),
                "epsilon_over_rc": epsilon,
                "D_over_epsilon_proxy": float(scale) / epsilon,
                "centerline_points": points,
                "local_minimum_count": len(minima),
                "candidate_surface_fraction_all_rays": scan["candidate_surface_fraction_all_rays"],
                "mean_minimum_rho_over_rc": (
                    float(np.mean([r["rho_over_rc"] for r in minima])) if minima else None
                ),
                "reach_estimate_over_rc": scan["reach_diagnostic"]["reach_estimate_over_rc"],
                "backend": scan["backend"]["backend"],
            })
    return {
        "schema": "sst.fermat.scale-sweep.v0.4.2",
        "package_version": PACKAGE_VERSION,
        "status": "RESEARCH_TRACK_SCALE_DIAGNOSTIC",
        "rows": rows,
        "results": results,
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }


def symmetry_audit(
    knot_id: str,
    *,
    epsilon: float = 0.0019,
    centerline_points: int = 4096,
    scale_over_rc: float = 1.0,
    force_python: bool = False,
    auto_build: bool = True,
) -> dict[str, Any]:
    curve = sample_ideal_knot(knot_id, centerline_points, scale_over_rc=scale_over_rc)
    rays, _ = _build_rays(curve, stations=2, angles=6)
    probes = np.vstack([r.origin + 0.0035 * r.radial_direction for r in rays])
    beta0, jac0, backend = _query_field_jacobian(
        curve, probes, epsilon=epsilon, force_python=force_python, auto_build=auto_build
    )

    transforms: dict[str, dict[str, float]] = {}
    translation = np.array([0.73, -0.21, 0.44])
    bt, jt, _ = _query_field_jacobian(
        curve + translation, probes + translation,
        epsilon=epsilon, force_python=force_python, auto_build=False,
    )
    transforms["translation"] = {
        "beta_linf_error": float(np.max(np.abs(bt - beta0))),
        "jacobian_linf_error": float(np.max(np.abs(jt - jac0))),
    }

    angle = 0.731
    axis = _unit(np.array([0.2, 0.7, -0.3]))
    kx = np.array([[0.0, -axis[2], axis[1]], [axis[2], 0.0, -axis[0]], [-axis[1], axis[0], 0.0]])
    rotation = np.eye(3) + math.sin(angle) * kx + (1.0 - math.cos(angle)) * (kx @ kx)
    cr = curve @ rotation.T
    pr = probes @ rotation.T
    br, jr, _ = _query_field_jacobian(
        cr, pr, epsilon=epsilon, force_python=force_python, auto_build=False
    )
    beta_expected = beta0 @ rotation.T
    jac_expected = np.einsum("ab,nbc,dc->nad", rotation, jac0, rotation)
    transforms["rotation"] = {
        "beta_linf_error": float(np.max(np.abs(br - beta_expected))),
        "jacobian_linf_error": float(np.max(np.abs(jr - jac_expected))),
    }

    shift = max(1, centerline_points // 7)
    bc, jc, _ = _query_field_jacobian(
        np.roll(curve, shift, axis=0), probes,
        epsilon=epsilon, force_python=force_python, auto_build=False,
    )
    transforms["cyclic_reindex"] = {
        "beta_linf_error": float(np.max(np.abs(bc - beta0))),
        "jacobian_linf_error": float(np.max(np.abs(jc - jac0))),
    }

    bo, jo, _ = _query_field_jacobian(
        curve[::-1].copy(), probes,
        epsilon=epsilon, force_python=force_python, auto_build=False,
    )
    transforms["orientation_reversal"] = {
        "beta_linf_error_against_sign_flip": float(np.max(np.abs(bo + beta0))),
        "jacobian_linf_error_against_sign_flip": float(np.max(np.abs(jo + jac0))),
        "beta_magnitude_linf_error": float(
            np.max(np.abs(np.linalg.norm(bo, axis=1) - np.linalg.norm(beta0, axis=1)))
        ),
    }

    reflection = np.diag([-1.0, 1.0, 1.0])
    bm, jm, _ = _query_field_jacobian(
        curve @ reflection.T, probes @ reflection.T,
        epsilon=epsilon, force_python=force_python, auto_build=False,
    )
    det = float(np.linalg.det(reflection))
    bm_expected = det * (beta0 @ reflection.T)
    jm_expected = det * np.einsum("ab,nbc,dc->nad", reflection, jac0, reflection)
    transforms["mirror"] = {
        "beta_linf_error_axial_transform": float(np.max(np.abs(bm - bm_expected))),
        "jacobian_linf_error_axial_transform": float(np.max(np.abs(jm - jm_expected))),
        "beta_magnitude_linf_error": float(
            np.max(np.abs(np.linalg.norm(bm, axis=1) - np.linalg.norm(beta0, axis=1)))
        ),
    }
    beta_errors = []
    jac_errors = []
    for row in transforms.values():
        beta_errors.extend(v for k, v in row.items() if "beta_linf_error" in k and "magnitude" not in k)
        jac_errors.extend(v for k, v in row.items() if "jacobian_linf_error" in k)
    return {
        "schema": "sst.fermat.symmetry-audit.v0.4.2",
        "package_version": PACKAGE_VERSION,
        "status": "RESEARCH_TRACK_NUMERICAL_INVARIANCE_AUDIT",
        "knot_id": knot_id,
        "backend": backend,
        "settings": {
            "epsilon_over_rc": epsilon,
            "centerline_points": centerline_points,
            "scale_over_rc": scale_over_rc,
        },
        "transforms": transforms,
        "max_beta_covariance_linf_error": max(beta_errors, default=0.0),
        "max_jacobian_covariance_linf_error": max(jac_errors, default=0.0),
        "passed": max(beta_errors, default=0.0) < 1e-10 and max(jac_errors, default=0.0) < 1e-8,
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }
