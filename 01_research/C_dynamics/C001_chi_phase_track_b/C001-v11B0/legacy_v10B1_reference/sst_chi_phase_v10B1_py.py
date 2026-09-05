#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SST chi-phase package v10B.1
Track B: corrected GP/NLSE core energy and ring-alpha extraction.

This module is a patch of v10B.0.  The decisive correction is the
interaction/depletion coefficient in the GP energy functional.

Solved ODE:
    F'' + F'/r - F/r^2 + F(1-F^2) = 0.

Consistent dimensionless energy density per pi*rho0*(hbar/m)^2:
    F^2/r + F'^2*r + 1/2*(F^2-1)^2*r.

v10B.0 used 1/4 in the last term, which is inconsistent with the ODE above
and artificially shifted alpha_GP upward to ~1.867.  v10B.1 uses 1/2 and adds
an asymptotic 1/R^2 + 1/R^4 extrapolation for the algebraic vortex tail.

Status: Research Track / CANON-compatible effective-core model.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.integrate import solve_bvp, trapezoid

PHI = (1.0 + math.sqrt(5.0)) / 2.0
A0_STAR = (math.sqrt(385.0) - 13.0) / 4.0
NLS_ALPHA_LEGACY = 1.61
NLS_BETA_LEGACY = 0.61

# Coefficients for energy density.  The ODE coefficient is 1.0 in F(1-F^2).
# Variation of lambda*(F^2-1)^2*r gives 2*lambda*F(F^2-1)*r,
# therefore lambda_energy = lambda_ODE/2 = 1/2.
ODE_NONLINEAR_COEFF = 1.0
ENERGY_INTERACTION_COEFF_CORRECTED = ODE_NONLINEAR_COEFF / 2.0
ENERGY_INTERACTION_COEFF_V10B0 = ODE_NONLINEAR_COEFF / 4.0


def _gp_rhs(r: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Right-hand side for scipy solve_bvp: y = [F, F']."""
    F, Fp = y
    r_safe = np.where(r < 1.0e-12, 1.0e-12, r)
    Fpp = -Fp / r_safe + F / r_safe**2 - F * (1.0 - F**2)
    return np.vstack([Fp, Fpp])


def _gp_bc(ya: np.ndarray, yb: np.ndarray, r_left: float = 0.02) -> np.ndarray:
    """Boundary conditions using near-axis F ~ C*r and far-field F -> 1."""
    return np.array([ya[0] - ya[1] * r_left, yb[0] - 1.0])


def solve_gp_profile(
    r_left: float = 0.02,
    r_right: float = 80.0,
    n_init: int = 1600,
    tol: float = 1.0e-8,
    max_nodes: int = 100_000,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
    """Solve the GP vortex ODE on [r_left, r_right]."""
    r_init = np.linspace(r_left, r_right, n_init)
    F_pade = r_init / np.sqrt(r_init**2 + 2.0)
    Fp_pade = 2.0 / (r_init**2 + 2.0)**1.5
    y_init = np.vstack([F_pade, Fp_pade])

    def bc(ya: np.ndarray, yb: np.ndarray) -> np.ndarray:
        return _gp_bc(ya, yb, r_left=r_left)

    sol = solve_bvp(_gp_rhs, bc, r_init, y_init,
                    tol=tol, verbose=0, max_nodes=max_nodes)
    return sol.x, sol.y[0], sol.y[1], bool(sol.success)


def compute_C_GP(
    r: np.ndarray,
    F: np.ndarray,
    Fp: np.ndarray,
    R_max: float,
    n_interp: int = 40_000,
    interaction_coeff: float = ENERGY_INTERACTION_COEFF_CORRECTED,
) -> Dict[str, float]:
    """Compute GP core constant using the requested interaction coefficient.

    Corrected v10B.1 convention:
        C_GP = int_0^R [F^2/r + F'^2*r + 1/2*(F^2-1)^2*r] dr - ln(R).

    The ring constant is alpha_GP = 2 - C_GP for a = xi.
    """
    R_use = min(float(R_max), float(r[-1] - 0.5))
    if R_use <= r[0]:
        raise ValueError("R_max is too small for the profile grid.")

    r_fine = np.linspace(float(r[0]), R_use, n_interp)
    F_fine = np.interp(r_fine, r, F)
    Fp_fine = np.interp(r_fine, r, Fp)

    integ_kin = F_fine**2 / r_fine
    integ_grad = Fp_fine**2 * r_fine
    integ_int = (F_fine**2 - 1.0)**2 * r_fine * interaction_coeff

    I_kin = float(trapezoid(integ_kin, r_fine))
    I_grad = float(trapezoid(integ_grad, r_fine))
    I_int = float(trapezoid(integ_int, r_fine))

    C_kin = I_kin - math.log(r_fine[-1])
    C_GP = C_kin + I_grad + I_int
    alpha = 2.0 - C_GP
    beta = alpha - 1.0  # q = 0 line from v8

    return {
        "C_GP": C_GP,
        "C_kin": C_kin,
        "C_grad": I_grad,
        "C_int": I_int,
        "C_decomp_sum": C_kin + I_grad + I_int,
        "alpha_GP_a_eq_xi": alpha,
        "beta_GP_q0_a_eq_xi": beta,
        "interaction_coeff": interaction_coeff,
        "R_max_used": float(r_fine[-1]),
        "NLS_legacy_alpha": NLS_ALPHA_LEGACY,
        "NLS_legacy_beta": NLS_BETA_LEGACY,
        "delta_alpha_raw": alpha - NLS_ALPHA_LEGACY,
        "delta_beta_q0": beta - NLS_BETA_LEGACY,
        "a_eff_to_match_NLS_xi": math.exp(2.0 - C_GP - NLS_ALPHA_LEGACY),
        "virial_ratio_grad_int": I_grad / I_int if I_int > 0 else float("nan"),
    }


def convergence_table(
    r: np.ndarray,
    F: np.ndarray,
    Fp: np.ndarray,
    R_values: Optional[List[float]] = None,
    n_interp: int = 30_000,
) -> List[Dict[str, float]]:
    """Compute corrected and v10B.0-legacy constants over R_max values."""
    if R_values is None:
        R_values = [8.0, 10.0, 12.0, 15.5, 20.0, 30.0, 40.0, 60.0, 70.0]
    rows: List[Dict[str, float]] = []
    for Rv in R_values:
        if Rv > r[-1] - 0.5:
            continue
        corr = compute_C_GP(r, F, Fp, Rv, n_interp=n_interp,
                            interaction_coeff=ENERGY_INTERACTION_COEFF_CORRECTED)
        old = compute_C_GP(r, F, Fp, Rv, n_interp=n_interp,
                           interaction_coeff=ENERGY_INTERACTION_COEFF_V10B0)
        rows.append({
            "R_max": Rv,
            "C_GP_corrected": corr["C_GP"],
            "alpha_GP_corrected": corr["alpha_GP_a_eq_xi"],
            "beta_GP_corrected_q0": corr["beta_GP_q0_a_eq_xi"],
            "C_GP_v10B0_coeff": old["C_GP"],
            "alpha_GP_v10B0_coeff": old["alpha_GP_a_eq_xi"],
            "delta_alpha_corrected_minus_NLS": corr["delta_alpha_raw"],
        })
    return rows


def asymptotic_fit(rows: List[Dict[str, float]], min_R: float = 12.0) -> Dict[str, float]:
    """Fit C(R)=C_inf+A/R^2+B/R^4 and return alpha_inf=2-C_inf.

    The GP vortex tail is algebraic, so this replaces the v10B.0 exponential
    convergence assumption.
    """
    xs = []
    ys = []
    for row in rows:
        R = float(row["R_max"])
        if R >= min_R:
            xs.append([1.0, 1.0/R**2, 1.0/R**4])
            ys.append(float(row["C_GP_corrected"]))
    if len(xs) < 3:
        raise ValueError("Need at least three convergence rows for asymptotic fit.")
    X = np.array(xs, dtype=float)
    y = np.array(ys, dtype=float)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    C_inf, A, B = map(float, coef)
    yhat = X @ coef
    rms = float(np.sqrt(np.mean((y - yhat)**2)))
    alpha_inf = 2.0 - C_inf
    beta_inf = alpha_inf - 1.0
    return {
        "fit_model": "C_GP(R)=C_inf+A/R^2+B/R^4",
        "min_R": min_R,
        "n_points": len(y),
        "C_inf": C_inf,
        "A": A,
        "B": B,
        "fit_rms": rms,
        "alpha_inf": alpha_inf,
        "beta_inf_q0": beta_inf,
        "delta_alpha_inf_minus_NLS": alpha_inf - NLS_ALPHA_LEGACY,
        "delta_beta_inf_minus_NLS": beta_inf - NLS_BETA_LEGACY,
        "a_eff_to_match_NLS_from_inf_xi": math.exp(alpha_inf - NLS_ALPHA_LEGACY),
    }


def pade_F(r: float | np.ndarray) -> float | np.ndarray:
    return r / np.sqrt(r**2 + 2.0)


def pade_Fp(r: float | np.ndarray) -> float | np.ndarray:
    return 2.0 / (r**2 + 2.0)**1.5


def pade_C_GP(R_max: float = 40.0, n: int = 50_000,
              interaction_coeff: float = ENERGY_INTERACTION_COEFF_CORRECTED) -> float:
    r = np.linspace(0.001, R_max, n)
    F = pade_F(r)
    Fp = pade_Fp(r)
    integ = F**2 / r + Fp**2 * r + (F**2 - 1.0)**2 * r * interaction_coeff
    return float(trapezoid(integ, r)) - math.log(R_max)


def profile_comparison_rows(r_gp: np.ndarray, F_gp: np.ndarray) -> List[Dict[str, float]]:
    r_check = [0.1, 0.2, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0, 12.0]
    rows: List[Dict[str, float]] = []
    for ri in r_check:
        if ri >= r_gp[-1]:
            continue
        F_exact = float(np.interp(ri, r_gp, F_gp))
        F_pade_val = float(pade_F(ri))
        rows.append({
            "r": ri,
            "F_exact": F_exact,
            "F_pade": F_pade_val,
            "delta_F": F_exact - F_pade_val,
            "rho_exact": F_exact**2,
            "rho_pade": F_pade_val**2,
        })
    return rows


def euler_benchmark_rows() -> List[Dict[str, float]]:
    return [
        {"model": "hollow_Euler", "C_core_analytic": 0.0,
         "alpha_analytic": 2.0, "alpha_formula": 2.0, "match": True},
        {"model": "Rankine_solid_Euler", "C_core_analytic": 0.25,
         "alpha_analytic": 7.0/4.0, "alpha_formula": 2.0 - 0.25,
         "match": abs(2.0 - 0.25 - 7.0/4.0) < 1e-14},
    ]


def energy_consistency_check() -> Dict[str, float | bool | str]:
    """Check the coefficient relation between the ODE and the energy."""
    expected = ODE_NONLINEAR_COEFF / 2.0
    ok = abs(ENERGY_INTERACTION_COEFF_CORRECTED - expected) < 1e-15
    return {
        "ODE_nonlinear_coeff": ODE_NONLINEAR_COEFF,
        "energy_interaction_coeff_expected": expected,
        "energy_interaction_coeff_used": ENERGY_INTERACTION_COEFF_CORRECTED,
        "v10B0_coeff": ENERGY_INTERACTION_COEFF_V10B0,
        "coeff_consistent": ok,
        "note": "variation of lambda*(F^2-1)^2*r gives ODE coefficient 2*lambda",
    }


def run_track_b(
    r_left: float = 0.02,
    r_right: float = 80.0,
    R_eval: float = 12.0,
    n_init: int = 1600,
    tol: float = 1.0e-8,
) -> Dict:
    r, F, Fp, success = solve_gp_profile(r_left=r_left, r_right=r_right,
                                         n_init=n_init, tol=tol)
    if not success:
        raise RuntimeError("GP BVP solver did not converge.")
    C1_star = float(F[0]) / float(r[0])
    core_corrected = compute_C_GP(r, F, Fp, R_max=R_eval,
                                  interaction_coeff=ENERGY_INTERACTION_COEFF_CORRECTED)
    core_v10B0 = compute_C_GP(r, F, Fp, R_max=R_eval,
                              interaction_coeff=ENERGY_INTERACTION_COEFF_V10B0)
    conv_rows = convergence_table(r, F, Fp)
    fit12 = asymptotic_fit(conv_rows, min_R=12.0)
    fit20 = asymptotic_fit(conv_rows, min_R=20.0)
    return {
        "success": success,
        "n_nodes_bvp": len(r),
        "r_left": r_left,
        "r_right": r_right,
        "R_eval": R_eval,
        "C1_star": C1_star,
        "pade_C1_star": 1.0 / math.sqrt(2.0),
        "core_results_corrected_R_eval": core_corrected,
        "core_results_v10B0_coeff_R_eval": core_v10B0,
        "convergence": conv_rows,
        "asymptotic_fit_minR12": fit12,
        "asymptotic_fit_minR20": fit20,
        "profile": profile_comparison_rows(r, F),
        "euler_benchmark": euler_benchmark_rows(),
        "energy_consistency": energy_consistency_check(),
    }


if __name__ == "__main__":
    import pprint
    pprint.pprint(run_track_b()["asymptotic_fit_minR12"])
