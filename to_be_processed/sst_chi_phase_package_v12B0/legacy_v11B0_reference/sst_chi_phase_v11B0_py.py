#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SST chi-phase package v11B.0
Track B: SST core-envelope -> GP/NLSE vortex ODE reduction audit.

Purpose
-------
v10B.1 showed that the corrected GP/NLSE core energy gives
alpha_ring^GP ~ 1.619 after algebraic-tail extrapolation.  v11B.0 tests the
next necessary step for a CANON-derived label: whether the solved GP/NLSE ODE
is the Euler-Lagrange equation of a canonical SST core-envelope functional.

Core functional
---------------
For a unit-winding core envelope Psi = F(r) exp(i theta), use the dimensionless
radial energy density

    L = A F'^2 r + B n^2 F^2/r + (C/2)(F^2 - 1)^2 r .

The Euler-Lagrange equation is

    F'' + F'/r - (B/A)n^2 F/r^2 + (C/A) F(1-F^2) = 0.

The v10B.1 GP ODE corresponds to A = B = C and n = 1.  Therefore the corrected
interaction coefficient 1/2 is not optional; it is required by variational
consistency.

Status: Research Track / CANON-compatibility audit.  Not locked CANON until
SST itself canonically fixes A=B=C for the internal core envelope.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import math
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.integrate import solve_bvp, trapezoid

PHI = (1.0 + math.sqrt(5.0)) / 2.0
A0_STAR = (math.sqrt(385.0) - 13.0) / 4.0
NLS_ALPHA_LEGACY = 1.61
NLS_BETA_LEGACY = 0.61


@dataclass(frozen=True)
class EnvelopeCoefficients:
    """Dimensionless coefficients of the SST core-envelope energy."""
    A_grad: float = 1.0
    B_phase: float = 1.0
    C_depletion: float = 1.0
    winding_n: int = 1

    @property
    def k_phase(self) -> float:
        return (self.B_phase / self.A_grad) * float(self.winding_n ** 2)

    @property
    def k_nonlinear(self) -> float:
        return self.C_depletion / self.A_grad

    @property
    def energy_interaction_coeff(self) -> float:
        # coefficient multiplying (F^2-1)^2*r in the radial energy after
        # normalizing A_grad=1.
        return self.C_depletion / (2.0 * self.A_grad)

    def is_gp_locked(self, tol: float = 1.0e-14) -> bool:
        return abs(self.k_phase - 1.0) < tol and abs(self.k_nonlinear - 1.0) < tol


def euler_lagrange_formula_row(coeff: EnvelopeCoefficients) -> Dict[str, float | str | bool]:
    """Return the derived ODE coefficients from the radial energy functional."""
    return {
        "A_grad": coeff.A_grad,
        "B_phase": coeff.B_phase,
        "C_depletion": coeff.C_depletion,
        "winding_n": coeff.winding_n,
        "k_phase_B_over_A_n2": coeff.k_phase,
        "k_nonlinear_C_over_A": coeff.k_nonlinear,
        "energy_interaction_coeff_C_over_2A": coeff.energy_interaction_coeff,
        "gp_ode_locked": coeff.is_gp_locked(),
        "derived_ODE": "F''+F'/r-k_phase*F/r^2+k_nonlinear*F*(1-F^2)=0",
    }


def energy_coefficient_consistency_rows() -> List[Dict[str, float | str | bool]]:
    """Compare v10B.0 and v10B.1 energy coefficients against the EL rule."""
    rows = []
    for name, k_ode, coeff_used in [
        ("v10B.0_old", 1.0, 0.25),
        ("v10B.1_corrected", 1.0, 0.50),
        ("general_example_half_ODE", 0.5, 0.25),
        ("general_example_double_ODE", 2.0, 1.00),
    ]:
        expected = k_ode / 2.0
        rows.append({
            "case": name,
            "ODE_nonlinear_coeff": k_ode,
            "energy_interaction_coeff_used": coeff_used,
            "energy_interaction_coeff_expected": expected,
            "consistent": abs(coeff_used - expected) < 1e-14,
            "rule": "energy_coeff = ODE_nonlinear_coeff / 2",
        })
    return rows


def _general_gp_rhs(coeff: EnvelopeCoefficients):
    def rhs(r: np.ndarray, y: np.ndarray) -> np.ndarray:
        F, Fp = y
        r_safe = np.where(r < 1.0e-12, 1.0e-12, r)
        Fpp = -Fp / r_safe + coeff.k_phase * F / r_safe**2 - coeff.k_nonlinear * F * (1.0 - F**2)
        return np.vstack([Fp, Fpp])
    return rhs


def _gp_bc(ya: np.ndarray, yb: np.ndarray, r_left: float = 0.02) -> np.ndarray:
    return np.array([ya[0] - ya[1] * r_left, yb[0] - 1.0])


def solve_envelope_profile(
    coeff: EnvelopeCoefficients = EnvelopeCoefficients(),
    r_left: float = 0.02,
    r_right: float = 80.0,
    n_init: int = 1600,
    tol: float = 1.0e-8,
    max_nodes: int = 100_000,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
    """Solve the generalized envelope vortex ODE as a BVP."""
    r_init = np.linspace(r_left, r_right, n_init)
    # Generic smooth initial guess.  The scale is adjusted by k_nonlinear when positive.
    scale = math.sqrt(max(coeff.k_nonlinear, 1.0e-12))
    F_guess = (scale * r_init) / np.sqrt((scale * r_init)**2 + 2.0 * max(coeff.k_phase, 1e-12))
    Fp_guess = np.gradient(F_guess, r_init)
    y_init = np.vstack([F_guess, Fp_guess])

    def bc(ya: np.ndarray, yb: np.ndarray) -> np.ndarray:
        return _gp_bc(ya, yb, r_left=r_left)

    sol = solve_bvp(_general_gp_rhs(coeff), bc, r_init, y_init,
                    tol=tol, verbose=0, max_nodes=max_nodes)
    return sol.x, sol.y[0], sol.y[1], bool(sol.success)


def compute_core_constant(
    r: np.ndarray,
    F: np.ndarray,
    Fp: np.ndarray,
    R_max: float,
    coeff: EnvelopeCoefficients = EnvelopeCoefficients(),
    n_interp: int = 40_000,
) -> Dict[str, float]:
    """Compute C_core and alpha_ring for the generalized envelope energy.

    The energy is normalized by A_grad.  For the canonical GP-locked case,
    alpha_ring = 2 - C_core, with a=xi.
    """
    R_use = min(float(R_max), float(r[-1] - 0.5))
    if R_use <= r[0]:
        raise ValueError("R_max is too small for the profile grid.")
    r_fine = np.linspace(float(r[0]), R_use, n_interp)
    F_fine = np.interp(r_fine, r, F)
    Fp_fine = np.interp(r_fine, r, Fp)

    # normalized by A_grad
    integ_kin = coeff.k_phase * F_fine**2 / r_fine
    integ_grad = Fp_fine**2 * r_fine
    integ_int = coeff.energy_interaction_coeff * (F_fine**2 - 1.0)**2 * r_fine

    I_kin = float(trapezoid(integ_kin, r_fine))
    I_grad = float(trapezoid(integ_grad, r_fine))
    I_int = float(trapezoid(integ_int, r_fine))
    C_kin = I_kin - coeff.k_phase * math.log(r_fine[-1])
    C_core = C_kin + I_grad + I_int

    # For the canonical n=1 GP normalization k_phase=k_nonlinear=1, this is
    # the classic alpha_ring formula.  For non-locked coefficient scans this is
    # a diagnostic, not a physical ring constant.
    alpha = 2.0 - C_core
    beta_q0 = alpha - 1.0
    return {
        "R_max_used": float(r_fine[-1]),
        "C_core": C_core,
        "C_kin_log_subtracted": C_kin,
        "C_grad": I_grad,
        "C_depletion": I_int,
        "alpha_ring_a_eq_xi": alpha,
        "beta_ring_q0": beta_q0,
        "k_phase": coeff.k_phase,
        "k_nonlinear": coeff.k_nonlinear,
        "energy_interaction_coeff": coeff.energy_interaction_coeff,
        "delta_alpha_minus_NLS": alpha - NLS_ALPHA_LEGACY,
        "delta_beta_minus_NLS": beta_q0 - NLS_BETA_LEGACY,
        "alpha_minus_phi": alpha - PHI,
    }


def convergence_table(
    r: np.ndarray,
    F: np.ndarray,
    Fp: np.ndarray,
    coeff: EnvelopeCoefficients = EnvelopeCoefficients(),
    R_values: Optional[List[float]] = None,
    n_interp: int = 30_000,
) -> List[Dict[str, float]]:
    if R_values is None:
        R_values = [8.0, 10.0, 12.0, 15.5, 20.0, 30.0, 40.0, 60.0, 70.0]
    rows = []
    for Rv in R_values:
        if Rv > r[-1] - 0.5:
            continue
        row = compute_core_constant(r, F, Fp, Rv, coeff=coeff, n_interp=n_interp)
        row["R_max"] = Rv
        rows.append(row)
    return rows


def asymptotic_fit(rows: List[Dict[str, float]], min_R: float = 12.0) -> Dict[str, float]:
    xs, ys = [], []
    for row in rows:
        R = float(row["R_max"])
        if R >= min_R:
            xs.append([1.0, 1.0/R**2, 1.0/R**4])
            ys.append(float(row["C_core"]))
    if len(xs) < 3:
        raise ValueError("Need at least three rows for fit.")
    X = np.asarray(xs)
    y = np.asarray(ys)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    C_inf, A, B = map(float, coef)
    yhat = X @ coef
    rms = float(np.sqrt(np.mean((y-yhat)**2)))
    alpha_inf = 2.0 - C_inf
    beta_inf = alpha_inf - 1.0
    return {
        "fit_model": "C_core(R)=C_inf+A/R^2+B/R^4",
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
        "alpha_inf_minus_phi": alpha_inf - PHI,
    }


def residual_table(
    r: np.ndarray,
    F: np.ndarray,
    Fp: np.ndarray,
    coeff: EnvelopeCoefficients = EnvelopeCoefficients(),
    n_samples: int = 2000,
) -> Dict[str, float]:
    """Numerically estimate ODE residual on an interpolated grid.

    Uses finite differences on Fp for F''.  This is only a smoke-test; the BVP
    residual from solve_bvp is the stronger internal criterion.
    """
    r_use = np.linspace(float(r[5]), float(min(r[-6], 40.0)), n_samples)
    F_use = np.interp(r_use, r, F)
    Fp_use = np.interp(r_use, r, Fp)
    Fpp_use = np.gradient(Fp_use, r_use)
    res = Fpp_use + Fp_use/r_use - coeff.k_phase*F_use/r_use**2 + coeff.k_nonlinear*F_use*(1.0-F_use**2)
    return {
        "residual_max_abs": float(np.max(np.abs(res))),
        "residual_rms": float(np.sqrt(np.mean(res**2))),
        "n_samples": int(n_samples),
        "r_min": float(r_use[0]),
        "r_max": float(r_use[-1]),
    }


def coefficient_scan_rows() -> List[Dict[str, float | bool | str]]:
    """Small coefficient-lock table.  This is not a fit; it shows which assumptions
    recover the canonical GP ODE.
    """
    cases = [
        ("canonical_SST_GP_lock", EnvelopeCoefficients(1.0, 1.0, 1.0, 1)),
        ("phase_stiffer_B_1p10", EnvelopeCoefficients(1.0, 1.10, 1.0, 1)),
        ("depletion_stiffer_C_1p10", EnvelopeCoefficients(1.0, 1.0, 1.10, 1)),
        ("old_energy_coeff_would_imply_C_0p50", EnvelopeCoefficients(1.0, 1.0, 0.50, 1)),
        ("double_winding_n2", EnvelopeCoefficients(1.0, 1.0, 1.0, 2)),
    ]
    rows = []
    for name, coeff in cases:
        row = euler_lagrange_formula_row(coeff)
        row["case"] = name
        row["canonical_residual_abs_kphase_minus_1"] = abs(coeff.k_phase - 1.0)
        row["canonical_residual_abs_knl_minus_1"] = abs(coeff.k_nonlinear - 1.0)
        rows.append(row)
    return rows


def run_v11B0(
    r_left: float = 0.02,
    r_right: float = 80.0,
    R_eval: float = 15.5,
    n_init: int = 1600,
    tol: float = 1e-8,
) -> Dict:
    coeff = EnvelopeCoefficients()
    r, F, Fp, success = solve_envelope_profile(coeff, r_left=r_left, r_right=r_right,
                                                n_init=n_init, tol=tol)
    if not success:
        raise RuntimeError("Envelope BVP solver did not converge.")
    core = compute_core_constant(r, F, Fp, R_eval, coeff=coeff)
    conv = convergence_table(r, F, Fp, coeff=coeff)
    fit12 = asymptotic_fit(conv, min_R=12.0)
    fit20 = asymptotic_fit(conv, min_R=20.0)
    return {
        "package": "v11B.0",
        "track": "B",
        "success": success,
        "n_nodes_bvp": len(r),
        "r_left": r_left,
        "r_right": r_right,
        "R_eval": R_eval,
        "C1_star": float(F[0]/r[0]),
        "coefficients": asdict(coeff),
        "euler_lagrange": [euler_lagrange_formula_row(coeff)],
        "energy_consistency": energy_coefficient_consistency_rows(),
        "coefficient_scan": coefficient_scan_rows(),
        "core_results": core,
        "convergence": conv,
        "asymptotic_fit_minR12": fit12,
        "asymptotic_fit_minR20": fit20,
        "residual": residual_table(r, F, Fp, coeff=coeff),
    }


if __name__ == "__main__":
    import pprint
    pprint.pprint(run_v11B0()["asymptotic_fit_minR12"])
