from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from typing import Any, Callable, Sequence

import numpy as np

from .core import PACKAGE_VERSION, backend_biot_savart_with_jacobian


class ClockDomainError(RuntimeError):
    """Raised when a ray integration leaves the real clock domain S^2>0."""


@dataclass(frozen=True)
class RayState:
    position: np.ndarray
    direction: np.ndarray


ClockEvaluator = Callable[[np.ndarray], tuple[float, np.ndarray, dict[str, Any]]]


def _unit(v: np.ndarray, *, name: str = "vector") -> np.ndarray:
    a = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(a))
    if not math.isfinite(n) or n <= 0.0:
        raise ValueError(f"{name} must have nonzero finite norm")
    return a / n


def make_clock_evaluator(
    curve: np.ndarray,
    *,
    epsilon: float,
    kernel_model: str = "rosenhead_midpoint",
    force_python: bool = False,
    auto_build: bool = True,
    minimum_s2: float = 1e-14,
) -> ClockEvaluator:
    """Create S and grad(S) evaluator for the full non-axisymmetric knot field.

    The Fermat metric used by this release is conformally Euclidean,
    ``g_F = S^{-2} delta`` with ``S=sqrt(1-|beta|^2)``.  The returned
    evaluator preserves the backend metadata from the first field call.
    """
    c = np.asarray(curve, dtype=float)
    if c.ndim != 2 or c.shape[1] != 3 or len(c) < 3:
        raise ValueError("curve must have shape (N,3), N>=3")
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    backend_cache: dict[str, Any] | None = None

    def evaluate(point: np.ndarray) -> tuple[float, np.ndarray, dict[str, Any]]:
        nonlocal backend_cache
        p = np.asarray(point, dtype=float).reshape(1, 3)
        beta, jac, backend = backend_biot_savart_with_jacobian(
            c.tolist(), p.tolist(), epsilon=epsilon, kernel_model=kernel_model,
            force_python=force_python, auto_build=auto_build if backend_cache is None else False,
        )
        if backend_cache is None:
            backend_cache = backend
        b = np.asarray(beta, dtype=float)[0]
        j = np.asarray(jac, dtype=float)[0]
        s2 = 1.0 - float(np.dot(b, b))
        if not math.isfinite(s2) or s2 <= minimum_s2:
            raise ClockDomainError(f"real clock domain violated: S^2={s2!r}")
        s = math.sqrt(s2)
        grad_s = -(j.T @ b) / s
        meta = {
            "backend": backend_cache,
            "beta": b,
            "jacobian": j,
            "S2": s2,
            "S": s,
            "grad_S": grad_s,
        }
        return s, grad_s, meta

    return evaluate


def ray_rhs(state: np.ndarray, clock_evaluator: ClockEvaluator) -> tuple[np.ndarray, dict[str, Any]]:
    """Euclidean-arclength ray equation for n=1/S.

    With unit tangent t and Euclidean arclength ell,

        dx/dell = t,
        dt/dell = -(I-t t^T) grad(S)/S.
    """
    y = np.asarray(state, dtype=float)
    x = y[:3]
    t = _unit(y[3:], name="ray direction")
    s, grad_s, meta = clock_evaluator(x)
    projector = np.eye(3) - np.outer(t, t)
    acceleration = -(projector @ grad_s) / s
    return np.concatenate([t, acceleration]), meta


def integrate_ray(
    initial_position: Sequence[float],
    initial_direction: Sequence[float],
    *,
    path_length: float,
    step_count: int,
    clock_evaluator: ClockEvaluator,
    record_stride: int = 1,
) -> dict[str, Any]:
    """Integrate a full 3-D Fermat ray with fixed-step RK4.

    Coordinates and path length are dimensionless in units of r_c.  The tangent
    is renormalized after each step; the accumulated norm correction is reported.
    """
    if path_length <= 0 or not math.isfinite(path_length):
        raise ValueError("path_length must be positive and finite")
    if step_count < 4:
        raise ValueError("step_count>=4 required")
    if record_stride < 1:
        raise ValueError("record_stride>=1 required")
    y = np.concatenate([
        np.asarray(initial_position, dtype=float),
        _unit(np.asarray(initial_direction, dtype=float), name="initial direction"),
    ])
    h = float(path_length) / int(step_count)
    trajectory: list[list[float]] = [y.tolist()]
    optical_length = 0.0
    max_tangent_norm_error = 0.0
    min_s = math.inf
    max_beta = 0.0
    backend: dict[str, Any] | None = None

    try:
        for i in range(step_count):
            k1, m1 = ray_rhs(y, clock_evaluator)
            k2, m2 = ray_rhs(y + 0.5 * h * k1, clock_evaluator)
            k3, m3 = ray_rhs(y + 0.5 * h * k2, clock_evaluator)
            k4, m4 = ray_rhs(y + h * k3, clock_evaluator)
            y_new = y + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
            tangent_norm = float(np.linalg.norm(y_new[3:]))
            max_tangent_norm_error = max(max_tangent_norm_error, abs(tangent_norm - 1.0))
            y_new[3:] = _unit(y_new[3:], name="integrated direction")
            optical_length += (h / 6.0) * (
                1.0 / float(m1["S"]) + 2.0 / float(m2["S"])
                + 2.0 / float(m3["S"]) + 1.0 / float(m4["S"])
            )
            for meta in (m1, m2, m3, m4):
                min_s = min(min_s, float(meta["S"]))
                max_beta = max(max_beta, float(np.linalg.norm(meta["beta"])))
                if backend is None:
                    backend = meta.get("backend")
            y = y_new
            if (i + 1) % record_stride == 0 or i + 1 == step_count:
                trajectory.append(y.tolist())
    except ClockDomainError as exc:
        return {
            "schema": "sst.fermat.ray-integration.v0.6.0",
            "package_version": PACKAGE_VERSION,
            "status": "CLOCK_DOMAIN_EXIT",
            "message": str(exc),
            "completed_steps": i if 'i' in locals() else 0,
            "requested_steps": step_count,
            "path_length_over_rc": path_length,
            "trajectory": trajectory,
            "global_closed_orbit_certified": False,
            "qsm_certified": False,
        }

    return {
        "schema": "sst.fermat.ray-integration.v0.6.0",
        "package_version": PACKAGE_VERSION,
        "status": "COMPLETED",
        "backend": backend,
        "initial_position_over_rc": np.asarray(initial_position, dtype=float).tolist(),
        "initial_direction": _unit(np.asarray(initial_direction, dtype=float)).tolist(),
        "final_position_over_rc": y[:3].tolist(),
        "final_direction": y[3:].tolist(),
        "path_length_over_rc": path_length,
        "optical_length_over_rc": optical_length,
        "step_count": step_count,
        "step_size_over_rc": h,
        "minimum_S": min_s,
        "maximum_beta_magnitude": max_beta,
        "max_tangent_norm_correction": max_tangent_norm_error,
        "trajectory": trajectory,
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }


def _shooting_basis(radial_direction: Sequence[float], tangent_seed: Sequence[float]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    t0 = _unit(np.asarray(tangent_seed, dtype=float), name="azimuthal seed")
    e1_raw = np.asarray(radial_direction, dtype=float)
    e1_raw = e1_raw - float(np.dot(e1_raw, t0)) * t0
    e1 = _unit(e1_raw, name="radial shooting basis")
    e2 = _unit(np.cross(t0, e1), name="axial shooting basis")
    return t0, e1, e2


def _state_from_parameters(
    base_position: np.ndarray,
    base_direction: np.ndarray,
    e1: np.ndarray,
    e2: np.ndarray,
    base_period: float,
    params: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, float]:
    x0 = base_position + params[0] * e1 + params[1] * e2
    t0 = _unit(base_direction + params[2] * e1 + params[3] * e2, name="shot direction")
    period = base_period * math.exp(float(params[4]))
    return x0, t0, period


def shoot_closed_orbit(
    curve: np.ndarray,
    seed: dict[str, Any],
    *,
    epsilon: float,
    step_count: int = 512,
    max_iterations: int = 10,
    position_tolerance_over_rc: float = 1e-7,
    direction_tolerance: float = 1e-7,
    force_python: bool = False,
    auto_build: bool = True,
    initial_parameters: Sequence[float] | None = None,
    finite_difference_scale: float = 2e-4,
    damping: float = 1e-4,
) -> dict[str, Any]:
    """Damped Gauss--Newton shooting from a local radial-minimum orbit seed.

    The five shooting variables are two transverse starting-position shifts, two
    direction tilts, and log(period/base_period).  The closure residual contains
    three position components and two transverse direction components.
    """
    c = np.asarray(curve, dtype=float)
    base_x = np.asarray(seed["position_over_rc"], dtype=float)
    radial = np.asarray(seed["radial_direction"], dtype=float)
    direction_values = seed.get("directions")
    base_t_raw = direction_values[0] if direction_values else seed["azimuthal_seed_direction"]
    base_t, e1, e2 = _shooting_basis(radial, base_t_raw)
    rho = float(seed["rho_over_rc"])
    base_period = 2.0 * math.pi * rho
    clock = make_clock_evaluator(
        c, epsilon=epsilon, force_python=force_python, auto_build=auto_build,
    )
    params = np.zeros(5, dtype=float) if initial_parameters is None else np.asarray(initial_parameters, dtype=float).copy()
    if params.shape != (5,):
        raise ValueError("initial_parameters must contain five values")
    fd = np.asarray([
        finite_difference_scale * max(rho, 1e-6),
        finite_difference_scale * max(rho, 1e-6),
        finite_difference_scale,
        finite_difference_scale,
        finite_difference_scale,
    ])
    history: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None

    def evaluate(z: np.ndarray, *, keep_trajectory: bool = False) -> tuple[np.ndarray | None, dict[str, Any]]:
        x0, t0, period = _state_from_parameters(base_x, base_t, e1, e2, base_period, z)
        integ = integrate_ray(
            x0, t0, path_length=period, step_count=step_count,
            clock_evaluator=clock,
            record_stride=max(1, step_count // 256) if keep_trajectory else step_count,
        )
        if integ["status"] != "COMPLETED":
            return None, {"integration": integ, "parameters": z.tolist()}
        xf = np.asarray(integ["final_position_over_rc"], dtype=float)
        tf = np.asarray(integ["final_direction"], dtype=float)
        dx = xf - x0
        dt = tf - t0
        residual = np.asarray([
            dx[0] / max(rho, 1e-12),
            dx[1] / max(rho, 1e-12),
            dx[2] / max(rho, 1e-12),
            float(np.dot(dt, e1)),
            float(np.dot(dt, e2)),
        ])
        info = {
            "parameters": z.tolist(),
            "initial_position_over_rc": x0.tolist(),
            "initial_direction": t0.tolist(),
            "period_over_rc": period,
            "position_closure_vector_over_rc": dx.tolist(),
            "position_closure_norm_over_rc": float(np.linalg.norm(dx)),
            "direction_closure_norm": float(np.linalg.norm(dt)),
            "normalized_residual": residual.tolist(),
            "normalized_residual_norm": float(np.linalg.norm(residual)),
            "integration": integ,
        }
        return residual, info

    for iteration in range(max_iterations + 1):
        residual, info = evaluate(params, keep_trajectory=False)
        if residual is None:
            history.append({"iteration": iteration, "status": "CLOCK_DOMAIN_EXIT", **info})
            break
        record = {"iteration": iteration, "status": "EVALUATED", **{k: v for k, v in info.items() if k != "integration"}}
        history.append(record)
        if best is None or info["normalized_residual_norm"] < best["normalized_residual_norm"]:
            best = info
        if (
            info["position_closure_norm_over_rc"] <= position_tolerance_over_rc
            and info["direction_closure_norm"] <= direction_tolerance
        ):
            break
        if iteration == max_iterations:
            break

        jac = np.empty((5, 5), dtype=float)
        jac_ok = True
        for j in range(5):
            z = params.copy(); z[j] += fd[j]
            rj, _ = evaluate(z, keep_trajectory=False)
            if rj is None:
                jac_ok = False
                break
            jac[:, j] = (rj - residual) / fd[j]
        if not jac_ok or not np.all(np.isfinite(jac)):
            history[-1]["status"] = "JACOBIAN_EVALUATION_FAILED"
            break
        lhs = jac.T @ jac + damping * np.eye(5)
        rhs = -(jac.T @ residual)
        try:
            delta = np.linalg.solve(lhs, rhs)
        except np.linalg.LinAlgError:
            delta = np.linalg.lstsq(lhs, rhs, rcond=None)[0]
        # Conservative trust limits protect the local-seed interpretation.
        delta[0:2] = np.clip(delta[0:2], -0.25 * rho, 0.25 * rho)
        delta[2:4] = np.clip(delta[2:4], -0.25, 0.25)
        delta[4] = float(np.clip(delta[4], -0.25, 0.25))
        accepted = False
        for factor in (1.0, 0.5, 0.25, 0.125, 0.0625):
            trial = params + factor * delta
            rr, trial_info = evaluate(trial, keep_trajectory=False)
            if rr is not None and trial_info["normalized_residual_norm"] < info["normalized_residual_norm"]:
                params = trial
                history[-1]["accepted_step_factor"] = factor
                accepted = True
                break
        if not accepted:
            history[-1]["status"] = "NO_DESCENT_STEP"
            break

    if best is None:
        return {
            "schema": "sst.fermat.closed-orbit-shot.v0.6.0",
            "package_version": PACKAGE_VERSION,
            "status": "UNRESOLVED_CLOCK_DOMAIN_EXIT",
            "seed": seed,
            "history": history,
            "resolved_closed_orbit": False,
            "global_closed_orbit_certified": False,
            "qsm_certified": False,
        }

    _, final_info = evaluate(np.asarray(best["parameters"], dtype=float), keep_trajectory=True)
    resolved = (
        final_info["position_closure_norm_over_rc"] <= position_tolerance_over_rc
        and final_info["direction_closure_norm"] <= direction_tolerance
    )
    return {
        "schema": "sst.fermat.closed-orbit-shot.v0.6.0",
        "package_version": PACKAGE_VERSION,
        "status": "RESOLVED_CLOSED_ORBIT" if resolved else "UNRESOLVED_SHOOTING_RESIDUAL",
        "seed": seed,
        "epsilon_over_rc": epsilon,
        "step_count": step_count,
        "base_period_over_rc": base_period,
        "shooting_basis": {"tangent": base_t.tolist(), "e1": e1.tolist(), "e2": e2.tolist()},
        "position_tolerance_over_rc": position_tolerance_over_rc,
        "direction_tolerance": direction_tolerance,
        "best": final_info,
        "history": history,
        "resolved_closed_orbit": resolved,
        # A single-resolution shot is deliberately not called certified.
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
        "guard": (
            "RESOLVED_CLOSED_ORBIT is a single-discretization shooting result. "
            "Global certification requires the three-level orbit convergence gate."
        ),
    }


def certify_closed_orbit_convergence(
    curve: np.ndarray,
    seed: dict[str, Any],
    *,
    epsilon: float,
    step_counts: Sequence[int] = (256, 512, 1024),
    max_iterations: int = 10,
    position_tolerance_over_rc: float = 2e-7,
    direction_tolerance: float = 2e-7,
    parameter_relative_tolerance: float = 2e-3,
    force_python: bool = False,
    auto_build: bool = True,
) -> dict[str, Any]:
    counts = sorted(set(int(v) for v in step_counts))
    if len(counts) < 3 or counts[0] < 32:
        raise ValueError("step_counts must contain at least three values >=32")
    levels: list[dict[str, Any]] = []
    params: Sequence[float] | None = None
    for i, count in enumerate(counts):
        shot = shoot_closed_orbit(
            curve, seed, epsilon=epsilon, step_count=count, max_iterations=max_iterations,
            position_tolerance_over_rc=position_tolerance_over_rc,
            direction_tolerance=direction_tolerance,
            force_python=force_python, auto_build=auto_build if i == 0 else False,
            initial_parameters=params,
        )
        levels.append(shot)
        if "best" in shot:
            params = shot["best"]["parameters"]
    last_two = levels[-2:]
    both_resolved = all(bool(v.get("resolved_closed_orbit")) for v in last_two)
    if all("best" in v for v in last_two):
        p0 = np.asarray(last_two[0]["best"]["parameters"], dtype=float)
        p1 = np.asarray(last_two[1]["best"]["parameters"], dtype=float)
        parameter_drift = float(np.linalg.norm(p1 - p0) / max(np.linalg.norm(p1), 1.0))
        period_drift = abs(float(last_two[1]["best"]["period_over_rc"]) - float(last_two[0]["best"]["period_over_rc"])) / max(abs(float(last_two[1]["best"]["period_over_rc"])), 1e-30)
    else:
        parameter_drift = period_drift = math.inf
    certified = both_resolved and parameter_drift <= parameter_relative_tolerance and period_drift <= parameter_relative_tolerance
    return {
        "schema": "sst.fermat.closed-orbit-integration-convergence.v0.6.0",
        "package_version": PACKAGE_VERSION,
        "status": "INTEGRATION_CONVERGENCE_RESOLVED_CLOSED_ORBIT" if certified else "UNRESOLVED_OR_NOT_INTEGRATION_CONVERGED",
        "epsilon_over_rc": epsilon,
        "step_counts": counts,
        "levels": levels,
        "last_two_parameter_relative_drift": parameter_drift if math.isfinite(parameter_drift) else None,
        "last_two_period_relative_drift": period_drift if math.isfinite(period_drift) else None,
        "parameter_relative_tolerance": parameter_relative_tolerance,
        "integration_convergence_certified": certified,
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
        "guard": (
            "This gate resolves integration-step convergence at one fixed centerline discretization. "
            "Global orbit certification additionally requires centerline-resolution convergence."
        ),
    }


def certify_global_closed_orbit(
    knot_id: str,
    *,
    epsilon: float,
    centerline_point_counts: Sequence[int] = (2048, 4096, 8192),
    step_counts: Sequence[int] = (256, 512, 1024),
    candidate_angles: int = 8,
    candidate_angle_index: int = 0,
    max_iterations: int = 10,
    centerline_relative_tolerance: float = 2e-3,
    force_python: bool = False,
    auto_build: bool = True,
) -> dict[str, Any]:
    """Two-axis gate: ray-step convergence at three centerline resolutions."""
    from .certification import scan_stationary_candidates
    from .knot_catalog import sample_ideal_knot

    counts = sorted(set(int(v) for v in centerline_point_counts))
    if len(counts) < 3 or counts[0] < 256:
        raise ValueError("centerline_point_counts must contain at least three values >=256")
    levels: list[dict[str, Any]] = []
    for i, n in enumerate(counts):
        atlas = scan_stationary_candidates(
            knot_id, epsilon=epsilon, centerline_points=n, stations=1, angles=candidate_angles,
            rho_min=0.0005, rho_max=0.01, bracket_samples=96,
            force_python=force_python, auto_build=auto_build if i == 0 else False,
            reach_pair_points=min(1024, max(128, n // 4)),
        )
        roots = [
            r for r in atlas["roots"]
            if r["classification"] == "RESOLVED_LOCAL_MINIMUM"
            and r["station"] == 0 and r["angle_index"] == candidate_angle_index
        ]
        if not roots:
            levels.append({
                "centerline_points": n, "candidate_atlas": atlas,
                "status": "NO_RESOLVED_LOCAL_MINIMUM_SEED",
                "integration_convergence": None,
            })
            continue
        root = roots[0]
        seed = {
            **root,
            "directions": [root["azimuthal_seed_direction"], [-v for v in root["azimuthal_seed_direction"]]],
        }
        curve = sample_ideal_knot(knot_id, n)
        integ = certify_closed_orbit_convergence(
            curve, seed, epsilon=epsilon, step_counts=step_counts,
            max_iterations=max_iterations, force_python=force_python, auto_build=False,
        )
        levels.append({
            "centerline_points": n, "candidate_atlas": atlas, "seed": seed,
            "status": integ["status"], "integration_convergence": integ,
        })

    resolved_levels = [v for v in levels if v.get("integration_convergence") and v["integration_convergence"].get("integration_convergence_certified")]
    highest_two = levels[-2:]
    highest_two_resolved = (
        len(highest_two) == 2
        and all(v.get("integration_convergence") and v["integration_convergence"].get("integration_convergence_certified") for v in highest_two)
    )
    all_levels_integration_certified = all(
        v.get("integration_convergence") and v["integration_convergence"].get("integration_convergence_certified")
        for v in levels
    )
    if highest_two_resolved:
        a, b = highest_two[0], highest_two[1]
        shot_a = a["integration_convergence"]["levels"][-1]
        shot_b = b["integration_convergence"]["levels"][-1]
        period_a = float(shot_a["best"]["period_over_rc"]); period_b = float(shot_b["best"]["period_over_rc"])
        rho_a = float(a["seed"]["rho_over_rc"]); rho_b = float(b["seed"]["rho_over_rc"])
        x_a = np.asarray(shot_a["best"]["initial_position_over_rc"], dtype=float)
        x_b = np.asarray(shot_b["best"]["initial_position_over_rc"], dtype=float)
        period_drift = abs(period_b - period_a) / max(abs(period_b), 1e-30)
        seed_rho_drift = abs(rho_b - rho_a) / max(abs(rho_b), 1e-30)
        start_position_drift = float(np.linalg.norm(x_b - x_a) / max(np.linalg.norm(x_b), 1.0))
        centerline_converged = max(period_drift, seed_rho_drift, start_position_drift) <= centerline_relative_tolerance
    else:
        period_drift = seed_rho_drift = start_position_drift = math.inf
        centerline_converged = False
    certified = all_levels_integration_certified and highest_two_resolved and centerline_converged
    available_levels = [
        v for v in levels
        if v.get("integration_convergence")
        and v["integration_convergence"].get("levels")
        and "best" in v["integration_convergence"]["levels"][-1]
    ]
    highest_shot = None
    if available_levels:
        highest_shot = dict(available_levels[-1]["integration_convergence"]["levels"][-1])
        highest_shot["global_closed_orbit_certified"] = certified
    return {
        "schema": "sst.fermat.global-closed-orbit-convergence.v0.6.0",
        "package_version": PACKAGE_VERSION,
        "knot_id": knot_id,
        "epsilon_over_rc": epsilon,
        "centerline_point_counts": counts,
        "step_counts": sorted(set(int(v) for v in step_counts)),
        "levels": levels,
        "integration_certified_centerline_level_count": len(resolved_levels),
        "all_centerline_levels_integration_certified": all_levels_integration_certified,
        "last_two_period_relative_drift": period_drift if math.isfinite(period_drift) else None,
        "last_two_seed_rho_relative_drift": seed_rho_drift if math.isfinite(seed_rho_drift) else None,
        "last_two_start_position_relative_drift": start_position_drift if math.isfinite(start_position_drift) else None,
        "centerline_relative_tolerance": centerline_relative_tolerance,
        "highest_resolution_shot": highest_shot,
        "status": "GLOBAL_CLOSED_ORBIT_CERTIFIED" if certified else "GLOBAL_ORBIT_UNRESOLVED_OR_NOT_CONVERGED",
        "global_closed_orbit_certified": certified,
        "qsm_certified": False,
        "guard": "Closed-orbit certification is numerical and model-conditional; it does not certify a QSM pole.",
    }


def _reciprocal_pairing_residual(values: np.ndarray) -> float:
    vals = list(complex(v) for v in values)
    best = math.inf
    for perm in itertools.permutations(range(4)):
        # pair (0,1) and (2,3); duplicate permutations are harmless for four values.
        r = abs(vals[perm[0]] * vals[perm[1]] - 1.0) + abs(vals[perm[2]] * vals[perm[3]] - 1.0)
        best = min(best, float(r))
    return best


def compute_reduced_monodromy(
    curve: np.ndarray,
    orbit_shot: dict[str, Any],
    *,
    epsilon: float,
    position_perturbation_fraction: float = 2e-5,
    direction_perturbation: float = 2e-5,
    force_python: bool = False,
    auto_build: bool = True,
    allow_uncertified_diagnostic: bool = False,
) -> dict[str, Any]:
    if not bool(orbit_shot.get("global_closed_orbit_certified")) and not allow_uncertified_diagnostic:
        return {
            "schema": "sst.fermat.reduced-monodromy.v0.6.0",
            "package_version": PACKAGE_VERSION,
            "status": "SKIPPED_GLOBAL_ORBIT_NOT_CERTIFIED",
            "matrix": None,
            "eigenvalues": [],
            "classification": None,
            "orbit_globally_certified": False,
            "monodromy_certified": False,
            "qsm_certified": False,
            "guard": "Monodromy/Floquet analysis is not evaluated before global closed-orbit certification.",
        }
    if "best" not in orbit_shot:
        raise ValueError("orbit_shot has no resolved shooting state")
    best = orbit_shot["best"]
    x0 = np.asarray(best["initial_position_over_rc"], dtype=float)
    t0 = _unit(np.asarray(best["initial_direction"], dtype=float))
    period = float(best["period_over_rc"])
    step_count = int(orbit_shot["step_count"])
    basis = orbit_shot["shooting_basis"]
    e1 = _unit(np.asarray(basis["e1"], dtype=float))
    e2 = _unit(np.asarray(basis["e2"], dtype=float))
    rho = float(orbit_shot["seed"]["rho_over_rc"])
    pos_eps = position_perturbation_fraction * max(rho, 1e-8)
    dir_eps = direction_perturbation
    clock = make_clock_evaluator(curve, epsilon=epsilon, force_python=force_python, auto_build=auto_build)

    nominal = integrate_ray(x0, t0, path_length=period, step_count=step_count, clock_evaluator=clock, record_stride=step_count)
    if nominal["status"] != "COMPLETED":
        raise ClockDomainError("nominal orbit exits real clock domain during monodromy evaluation")
    x_nom = np.asarray(nominal["final_position_over_rc"], dtype=float)
    t_nom = np.asarray(nominal["final_direction"], dtype=float)

    columns: list[np.ndarray] = []
    perturbations = [
        (pos_eps * e1, np.zeros(3), pos_eps, "position_e1"),
        (pos_eps * e2, np.zeros(3), pos_eps, "position_e2"),
        (np.zeros(3), dir_eps * e1, dir_eps, "direction_e1"),
        (np.zeros(3), dir_eps * e2, dir_eps, "direction_e2"),
    ]
    column_meta: list[dict[str, Any]] = []
    for dx, dt, eps_value, name in perturbations:
        outputs = []
        for sign in (+1.0, -1.0):
            xi = x0 + sign * dx
            ti = _unit(t0 + sign * dt)
            flow = integrate_ray(xi, ti, path_length=period, step_count=step_count, clock_evaluator=clock, record_stride=step_count)
            if flow["status"] != "COMPLETED":
                raise ClockDomainError(f"perturbed orbit {name} exits real clock domain")
            xf = np.asarray(flow["final_position_over_rc"], dtype=float)
            tf = np.asarray(flow["final_direction"], dtype=float)
            outputs.append((xf, tf))
        dxf = (outputs[0][0] - outputs[1][0]) / (2.0 * eps_value)
        dtf = (outputs[0][1] - outputs[1][1]) / (2.0 * eps_value)
        if name.startswith("position"):
            dxf = dxf * max(rho, 1e-8)  # map normalized input position coordinate to normalized output
        column = np.asarray([
            float(np.dot(dxf, e1)) / max(rho, 1e-8),
            float(np.dot(dxf, e2)) / max(rho, 1e-8),
            float(np.dot(dtf, e1)),
            float(np.dot(dtf, e2)),
        ])
        columns.append(column)
        column_meta.append({"name": name, "perturbation": eps_value})
    matrix = np.column_stack(columns)
    eigenvalues = np.linalg.eigvals(matrix)
    moduli = np.abs(eigenvalues)
    spectral_radius = float(np.max(moduli))
    unit_circle_deviation = float(np.max(np.abs(moduli - 1.0)))
    reciprocal_residual = _reciprocal_pairing_residual(eigenvalues)
    if spectral_radius > 1.0 + 1e-2:
        classification = "HYPERBOLIC_OR_MIXED_DIAGNOSTIC"
    elif unit_circle_deviation < 1e-2:
        classification = "ELLIPTIC_OR_NEUTRAL_DIAGNOSTIC"
    else:
        classification = "MARGINAL_OR_UNRESOLVED_DIAGNOSTIC"
    return {
        "schema": "sst.fermat.reduced-monodromy.v0.6.0",
        "package_version": PACKAGE_VERSION,
        "status": "RESEARCH_TRACK_MONODROMY_DIAGNOSTIC",
        "orbit_resolved_single_level": bool(orbit_shot.get("resolved_closed_orbit")),
        "orbit_globally_certified": bool(orbit_shot.get("global_closed_orbit_certified")),
        "matrix": matrix.tolist(),
        "eigenvalues": [{"real": float(v.real), "imag": float(v.imag), "modulus": float(abs(v))} for v in eigenvalues],
        "determinant": float(np.linalg.det(matrix)),
        "spectral_radius": spectral_radius,
        "maximum_unit_circle_deviation": unit_circle_deviation,
        "reciprocal_pairing_residual": reciprocal_residual,
        "classification": classification,
        "column_metadata": column_meta,
        "nominal_flow_closure_position_over_rc": float(np.linalg.norm(x_nom - x0)),
        "nominal_flow_closure_direction": float(np.linalg.norm(t_nom - t0)),
        "monodromy_certified": False,
        "qsm_certified": False,
        "guard": (
            "The reduced 4x4 map is a fixed-period finite-difference diagnostic. "
            "Floquet certification requires perturbation and step-size convergence."
        ),
    }


def certify_monodromy_convergence(
    curve: np.ndarray,
    orbit_shot: dict[str, Any],
    *,
    epsilon: float,
    perturbation_scales: Sequence[float] = (4e-5, 2e-5, 1e-5),
    matrix_relative_tolerance: float = 5e-2,
    force_python: bool = False,
    auto_build: bool = True,
) -> dict[str, Any]:
    """Finite-difference perturbation convergence gate for the reduced map."""
    scales = sorted(set(float(v) for v in perturbation_scales), reverse=True)
    if len(scales) < 3 or any(v <= 0 for v in scales):
        raise ValueError("perturbation_scales must contain at least three positive values")
    levels = []
    for i, scale in enumerate(scales):
        result = compute_reduced_monodromy(
            curve, orbit_shot, epsilon=epsilon,
            position_perturbation_fraction=scale,
            direction_perturbation=scale,
            force_python=force_python,
            auto_build=auto_build if i == 0 else False,
        )
        levels.append(result)
    m0 = np.asarray(levels[-2]["matrix"], dtype=float)
    m1 = np.asarray(levels[-1]["matrix"], dtype=float)
    matrix_drift = float(np.linalg.norm(m1 - m0) / max(np.linalg.norm(m1), 1e-30))
    orbit_certified = bool(orbit_shot.get("global_closed_orbit_certified"))
    certified = orbit_certified and matrix_drift <= matrix_relative_tolerance
    return {
        "schema": "sst.fermat.monodromy-convergence.v0.6.0",
        "package_version": PACKAGE_VERSION,
        "status": "MONODROMY_CONVERGENCE_CERTIFIED" if certified else "MONODROMY_DIAGNOSTIC_NOT_CERTIFIED",
        "perturbation_scales": scales,
        "levels": levels,
        "last_two_matrix_relative_drift": matrix_drift,
        "matrix_relative_tolerance": matrix_relative_tolerance,
        "orbit_globally_certified": orbit_certified,
        "monodromy_certified": certified,
        "qsm_certified": False,
        "guard": "A certified monodromy map still does not constitute a complex-frequency QSM pole.",
    }
