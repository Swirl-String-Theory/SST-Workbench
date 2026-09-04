from __future__ import annotations

from itertools import product
import numpy as np

from .symplectic import linearized_hamiltonian_spectrum

TERM_NAMES = ("length", "bending", "tube_repulsion", "neumann")


def simplex_weights(dimension: int, resolution: int) -> list[np.ndarray]:
    """Deterministic rational grid on the nonnegative unit simplex."""
    if dimension < 1 or resolution < 1:
        raise ValueError("dimension and resolution must be positive")
    rows=[]
    def rec(prefix, remaining, slots):
        if slots == 1:
            rows.append(np.asarray(prefix+[remaining], dtype=float)/resolution)
            return
        for value in range(remaining+1):
            rec(prefix+[value], remaining-value, slots-1)
    rec([], resolution, dimension)
    return rows


def _cancellation_ratio(weights: np.ndarray, gradients: np.ndarray) -> float:
    contributions=weights[:,None]*gradients
    return float(np.linalg.norm(np.sum(contributions,axis=0))/max(np.sum(np.linalg.norm(contributions,axis=1)),1e-300))


def scan_sector_closure(
    sector: dict,
    resolution: int = 8,
    max_gradient_norm: float = 1.0,
    rank_tolerance: float = 1e-8,
    stability_tolerance: float = 1e-6,
) -> tuple[dict, list[dict]]:
    """Scan nonnegative normalized closure weights for one circulation sector.

    This is a robustness/fine-tuning diagnostic. It does not select physical weights.
    """
    finite=sector["energy_closure"]["finite_difference"]
    gradients=np.asarray([finite["gradients"][name]["vector"] for name in TERM_NAMES],dtype=float)
    hessians=np.asarray([finite["hessians"][name]["matrix"] for name in TERM_NAMES],dtype=float)
    omega=np.asarray(sector["candidate_symplectic_form"]["matrix"],dtype=float)
    scheme=str(finite["hessian_scheme"])
    rows=[]
    for index,weights in enumerate(simplex_weights(len(TERM_NAMES),resolution)):
        gradient=weights@gradients
        hessian=np.tensordot(weights,hessians,axes=(0,0))
        eig=np.linalg.eigvalsh(0.5*(hessian+hessian.T))
        spectrum=linearized_hamiltonian_spectrum(
            omega,hessian,rank_tolerance=rank_tolerance,
            stability_tolerance=stability_tolerance,hessian_scheme=scheme,
        )
        stationary=float(np.linalg.norm(gradient)) <= max_gradient_norm
        nonnegative=int(np.sum(eig < -1e-7)) == 0
        full_stable=bool(nonnegative and spectrum["spectrally_stable"])
        rows.append({
            "grid_index":index,
            **{f"w_{name}":float(weights[i]) for i,name in enumerate(TERM_NAMES)},
            "gradient_norm":float(np.linalg.norm(gradient)),
            "gradient_cancellation_ratio":_cancellation_ratio(weights,gradients),
            "minimum_hessian_eigenvalue":float(eig[0]),
            "negative_mode_count":int(np.sum(eig < -1e-7)),
            "stationary_screen":bool(stationary),
            "nonnegative_hessian_screen":bool(nonnegative),
            "spectrally_stable_screen":bool(spectrum["spectrally_stable_screen"]),
            "full_hessian_stability_claim":bool(full_stable),
            "hessian_scheme":scheme,
        })
    equal=np.full(len(TERM_NAMES),1.0/len(TERM_NAMES))
    best=min(rows,key=lambda row:row["gradient_norm"])
    stationary_fraction=float(np.mean([row["stationary_screen"] for row in rows]))
    nonnegative_fraction=float(np.mean([row["nonnegative_hessian_screen"] for row in rows]))
    stable_claim_fraction=float(np.mean([row["full_hessian_stability_claim"] for row in rows]))
    joint_fraction=float(np.mean([
        row["stationary_screen"] and row["full_hessian_stability_claim"] for row in rows
    ]))
    if scheme != "full-central": robustness="screening-only"
    elif joint_fraction >= 0.25: robustness="broad-closure-region"
    elif joint_fraction > 0: robustness="narrow-closure-region"
    else: robustness="no-stationary-stable-grid-point"
    summary={
        "signs":sector["sign_string"],
        "grid_resolution":int(resolution),
        "grid_point_count":len(rows),
        "hessian_scheme":scheme,
        "stationary_fraction":stationary_fraction,
        "nonnegative_hessian_screen_fraction":nonnegative_fraction,
        "full_hessian_stability_claim_fraction":stable_claim_fraction,
        "joint_stationary_stable_fraction":joint_fraction,
        "best_gradient_norm":best["gradient_norm"],
        "best_weights":{name:best[f"w_{name}"] for name in TERM_NAMES},
        "best_cancellation_ratio":best["gradient_cancellation_ratio"],
        "best_weight_distance_from_equal":float(np.linalg.norm(np.asarray([best[f"w_{n}"] for n in TERM_NAMES])-equal)),
        "robustness_class":robustness,
        "status":"[RESEARCH TRACK] Closure-simplex robustness; weights are not derived physical constants.",
    }
    return summary,rows


def borromean_sector_diagnostic(link_id: str, signs: list[int]) -> dict | None:
    if link_id != "L6a4" or len(signs) != 3:
        return None
    product_sign=int(np.prod(np.asarray(signs,dtype=int)))
    return {
        "common_name":"Borromean rings",
        "milnor_mu123_abs_catalog":1,
        "milnor_value_status":"[CATALOG REFERENCE, NOT NUMERICALLY COMPUTED]",
        "circulation_product":product_sign,
        "cubic_oriented_sector_proxy":product_sign,
        "global_circulation_reversal_parity":"odd",
        "interpretation":"[SPECULATIVE] mu_123*Gamma1*Gamma2*Gamma3 sector label; not an energy term or quantum amplitude.",
    }
