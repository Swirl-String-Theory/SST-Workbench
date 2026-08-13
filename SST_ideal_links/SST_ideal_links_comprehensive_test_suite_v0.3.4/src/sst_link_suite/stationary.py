from __future__ import annotations

import numpy as np

from .native_ext import BackendOptions
from .perturbations import ReducedBasis
from .qm_energy import central_profile_gradient_at_coordinates, evaluate_profile_at_coordinates


def stationary_newton_probe(
    samples, basis: ReducedBasis, signs: np.ndarray, diameter: float, epsilon: float,
    backend_options: BackendOptions, profile_weights: dict[str, float],
    normalization_scales: dict[str, float], baseline_gradient: np.ndarray,
    baseline_hessian: np.ndarray, cfg: dict,
) -> dict:
    """One trust-limited Newton direction plus nonlinear line search.

    This is intentionally a *probe*, not a geometry optimizer.  It asks whether the local
    full-Hessian model points toward a nearby configuration with a smaller actual gradient.
    """
    g = np.asarray(baseline_gradient, dtype=float)
    h = 0.5*(np.asarray(baseline_hessian, dtype=float)+np.asarray(baseline_hessian, dtype=float).T)
    q = -np.linalg.pinv(h, rcond=float(cfg.get("stationary_pinv_rcond", 1e-8))) @ g
    max_norm = float(cfg.get("stationary_max_coordinate_norm_D", 0.05)) * float(diameter)
    raw_norm = float(np.linalg.norm(q))
    if raw_norm > max_norm > 0:
        q *= max_norm/raw_norm
    step = float(cfg.get("stationary_gradient_step_D", cfg.get("finite_difference_refined_step_D", 0.001))) * float(diameter)
    line_factors = [float(x) for x in cfg.get("stationary_line_factors", [1.0, 0.5, 0.25, 0.125])]
    baseline_norm = float(np.linalg.norm(g))
    candidates = []
    for factor in line_factors:
        trial = factor*q
        grad = central_profile_gradient_at_coordinates(
            samples, basis, trial, signs, diameter, epsilon, backend_options,
            profile_weights, normalization_scales, step,
            local_skip_energy=int(cfg.get("local_skip_energy", 2)),
            self_exclusion_energy_arc_D=cfg.get("self_exclusion_energy_arc_D"),
            repulsion_softness=float(cfg.get("repulsion_softness_D", 0.04)),
            repulsion_margin=float(cfg.get("repulsion_margin", 0.0)),
            derivative_method=str(cfg.get("geometric_derivative_method", "spectral_fft")),
        )
        energy = evaluate_profile_at_coordinates(
            samples, basis, trial, signs, diameter, epsilon, backend_options,
            profile_weights, normalization_scales,
            local_skip_energy=int(cfg.get("local_skip_energy", 2)),
            self_exclusion_energy_arc_D=cfg.get("self_exclusion_energy_arc_D"),
            repulsion_softness=float(cfg.get("repulsion_softness_D", 0.04)),
            repulsion_margin=float(cfg.get("repulsion_margin", 0.0)),
            derivative_method=str(cfg.get("geometric_derivative_method", "spectral_fft")),
        )
        candidates.append({
            "line_factor": factor,
            "coordinate_norm_D": float(np.linalg.norm(trial)/max(diameter, 1e-300)),
            "gradient_norm": float(np.linalg.norm(grad)),
            "gradient_reduction_factor": float(np.linalg.norm(grad)/max(baseline_norm, 1e-300)),
            "profile_energy": float(energy),
            "coordinates": trial,
        })
    best = min(candidates, key=lambda x: x["gradient_norm"])
    return {
        "requested": True,
        "baseline_gradient_norm": baseline_norm,
        "raw_newton_coordinate_norm_D": raw_norm/max(diameter, 1e-300),
        "trust_limited_newton_coordinate_norm_D": float(np.linalg.norm(q)/max(diameter, 1e-300)),
        "candidates": candidates,
        "best": best,
        "improves_gradient": bool(best["gradient_norm"] < baseline_norm),
        "stationary_threshold": float(cfg.get("max_reduced_gradient_norm", 1.0)),
        "reaches_stationary_threshold": bool(best["gradient_norm"] <= float(cfg.get("max_reduced_gradient_norm", 1.0))),
        "status": (
            "[RESEARCH TRACK] Local trust-limited Newton probe in the reduced basis. "
            "It does not replace a constrained topology-preserving finite-core optimizer."
        ),
    }
