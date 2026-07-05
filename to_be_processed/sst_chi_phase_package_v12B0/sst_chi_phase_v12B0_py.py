#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SST chi-phase package v12B.0
Track B: GP/NLSE algebraic-tail and asymptotic alpha_ring extraction audit.

Purpose
-------
v10B.1 computed alpha_ring^GP after correcting the GP/NLSE energy coefficient.
v11B.0 showed that the solved ODE is the Euler-Lagrange equation of a canonical
core-envelope functional when A=B=C.  v12B.0 tests the next canon gate: the
large-r algebraic tail and the extrapolation law used to extract the infinite
core radius constant.

Canonical unit-winding ODE
--------------------------
    F'' + F'/r - F/r^2 + F(1-F^2) = 0,
    F(0)=0, F(infty)=1.

Asymptotic expansion
--------------------
    F(r) = 1 - 1/(2r^2) - 9/(8r^4) - 161/(16r^6) - ...

For the corrected GP/NLSE radial energy integrand
    I(r) = F^2/r + F'^2 r + 1/2(F^2-1)^2 r,
the log-subtracted core constant obeys
    C(R) = int_0^R I(r)dr - ln R,
    C_inf - C(R) = int_R^inf [I(r)-1/r]dr
                 = -1/(4R^2)+1/(4R^4)+11/(6R^6)+179/(8R^8)+...
Therefore
    C(R)=C_inf+1/(4R^2)-1/(4R^4)-11/(6R^6)-179/(8R^8)-...

Status: Strong Research Track / asymptotic extraction audit.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from fractions import Fraction
import math
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.integrate import solve_bvp, trapezoid

PHI = (1.0 + math.sqrt(5.0)) / 2.0
NLS_ALPHA_LEGACY = 1.61
NLS_BETA_LEGACY = 0.61

# F(r)=1+sum_k a_k r^(-2k).  First terms from substituting into the ODE.
F_TAIL_COEFFS: List[Tuple[int, Fraction]] = [
    (1, Fraction(-1, 2)),
    (2, Fraction(-9, 8)),
    (3, Fraction(-161, 16)),
    (4, Fraction(-24661, 128)),
    (5, Fraction(-1635111, 256)),
    (6, Fraction(-334291917, 1024)),
]

# I(r)-1/r = sum_j b_j r^(-p_j), where I is the corrected GP energy integrand.
ENERGY_TAIL_COEFFS: List[Tuple[int, Fraction]] = [
    (3, Fraction(-1, 2)),
    (5, Fraction(1, 1)),
    (7, Fraction(11, 1)),
    (9, Fraction(179, 1)),
    (11, Fraction(9109, 2)),
    (13, Fraction(177484, 1)),
    (15, Fraction(270252133, 256)),
]


@dataclass(frozen=True)
class EnvelopeCoefficients:
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
        return self.C_depletion / (2.0 * self.A_grad)


def tail_coefficient_rows() -> List[Dict[str, str | float | int]]:
    rows: List[Dict[str, str | float | int]] = []
    for k, a in F_TAIL_COEFFS:
        rows.append({
            "series": "F(r)=1+sum a_k r^(-2k)",
            "term_index_k": k,
            "power": -2*k,
            "coefficient_exact": f"{a.numerator}/{a.denominator}" if a.denominator != 1 else str(a.numerator),
            "coefficient_float": float(a),
        })
    for p, b in ENERGY_TAIL_COEFFS:
        # tail integral coefficient: int_R^inf b r^{-p} dr = b/(p-1) R^{-(p-1)}
        t = b / Fraction(p-1, 1)
        rows.append({
            "series": "I(r)-1/r=sum b_p r^(-p)",
            "term_index_k": (p-1)//2,
            "power": -p,
            "coefficient_exact": f"{b.numerator}/{b.denominator}" if b.denominator != 1 else str(b.numerator),
            "coefficient_float": float(b),
            "tail_integral_power": -(p-1),
            "tail_integral_coeff_exact": f"{t.numerator}/{t.denominator}" if t.denominator != 1 else str(t.numerator),
            "tail_integral_coeff_float": float(t),
        })
    return rows


def asymptotic_F(r: np.ndarray | float, max_k: int = 3) -> np.ndarray:
    rr = np.asarray(r, dtype=float)
    out = np.ones_like(rr)
    for k, a in F_TAIL_COEFFS[:max_k]:
        out += float(a) * rr ** (-2*k)
    return out


def energy_integrand_tail_minus_log(r: np.ndarray | float, max_terms: int = 4) -> np.ndarray:
    """Return asymptotic I(r)-1/r up to max_terms."""
    rr = np.asarray(r, dtype=float)
    out = np.zeros_like(rr)
    for p, b in ENERGY_TAIL_COEFFS[:max_terms]:
        out += float(b) * rr ** (-p)
    return out


def C_tail_correction(R: float, max_terms: int = 4) -> float:
    """Return C_inf-C(R)=int_R^inf [I(r)-1/r]dr using asymptotic terms."""
    s = 0.0
    for p, b in ENERGY_TAIL_COEFFS[:max_terms]:
        s += float(b) / float(p-1) * R ** (-(p-1))
    return s


def expected_C_fit_coeff_rows() -> List[Dict[str, float | str | int]]:
    """Expected coefficients in C(R)=C_inf + A2/R^2 + A4/R^4 + ... ."""
    rows = []
    for p, b in ENERGY_TAIL_COEFFS:
        # C(R)=C_inf - int_R^inf (I-1/r)dr
        coeff = -float(b) / float(p-1)
        power = -(p-1)
        rows.append({
            "model": "C(R)=C_inf+sum A_m R^{-m}",
            "m": p-1,
            "power": power,
            "A_m": coeff,
            "from_integrand_coeff_b_p": float(b),
        })
    return rows


def _gp_rhs(coeff: EnvelopeCoefficients):
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
    r_right: float = 160.0,
    n_init: int = 2200,
    tol: float = 1.0e-8,
    max_nodes: int = 150_000,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
    r_init = np.linspace(r_left, r_right, n_init)
    F_guess = r_init / np.sqrt(r_init**2 + 2.0)
    Fp_guess = np.gradient(F_guess, r_init)
    y_init = np.vstack([F_guess, Fp_guess])

    def bc(ya: np.ndarray, yb: np.ndarray) -> np.ndarray:
        return _gp_bc(ya, yb, r_left=r_left)

    sol = solve_bvp(_gp_rhs(coeff), bc, r_init, y_init,
                    tol=tol, verbose=0, max_nodes=max_nodes)
    return sol.x, sol.y[0], sol.y[1], bool(sol.success)


def compute_core_constant(
    r: np.ndarray,
    F: np.ndarray,
    Fp: np.ndarray,
    R_max: float,
    coeff: EnvelopeCoefficients = EnvelopeCoefficients(),
    n_interp: int = 50_000,
) -> Dict[str, float]:
    R_use = min(float(R_max), float(r[-1] - 2.0))
    if R_use <= r[0]:
        raise ValueError("R_max is too small for the profile grid.")
    r_fine = np.linspace(float(r[0]), R_use, n_interp)
    F_fine = np.interp(r_fine, r, F)
    Fp_fine = np.interp(r_fine, r, Fp)
    integ_kin = coeff.k_phase * F_fine**2 / r_fine
    integ_grad = Fp_fine**2 * r_fine
    integ_int = coeff.energy_interaction_coeff * (F_fine**2 - 1.0)**2 * r_fine
    I_kin = float(trapezoid(integ_kin, r_fine))
    I_grad = float(trapezoid(integ_grad, r_fine))
    I_int = float(trapezoid(integ_int, r_fine))
    C_kin = I_kin - coeff.k_phase * math.log(r_fine[-1])
    C_core = C_kin + I_grad + I_int
    alpha = 2.0 - C_core
    beta = alpha - 1.0
    row = {
        "R_max": R_use,
        "C_core": C_core,
        "C_kin_log_subtracted": C_kin,
        "C_grad": I_grad,
        "C_depletion": I_int,
        "alpha_ring_raw_R": alpha,
        "beta_ring_q0_raw_R": beta,
    }
    # Tail-corrected estimates of C_inf and alpha_inf using increasing orders.
    for n_terms in [1, 2, 3, 4, 5]:
        corr = C_tail_correction(R_use, max_terms=n_terms)
        C_est = C_core + corr
        row[f"tail_terms_{n_terms}_Cinf_est"] = C_est
        row[f"tail_terms_{n_terms}_alpha_inf_est"] = 2.0 - C_est
        row[f"tail_terms_{n_terms}_correction_Cinf_minus_C"] = corr
    return row


def convergence_table(
    r: np.ndarray,
    F: np.ndarray,
    Fp: np.ndarray,
    R_values: Optional[List[float]] = None,
    n_interp: int = 50_000,
) -> List[Dict[str, float]]:
    if R_values is None:
        R_values = [8.0, 10.0, 12.0, 15.5, 20.0, 30.0, 40.0, 60.0, 70.0, 90.0, 110.0, 130.0]
    rows = []
    for Rv in R_values:
        if Rv > r[-1] - 2.0:
            continue
        rows.append(compute_core_constant(r, F, Fp, Rv, n_interp=n_interp))
    return rows


def F_tail_validation_rows(r: np.ndarray, F: np.ndarray, sample_R: Optional[List[float]] = None) -> List[Dict[str, float]]:
    if sample_R is None:
        sample_R = [8.0, 10.0, 12.0, 15.5, 20.0, 30.0, 40.0, 60.0, 70.0, 90.0, 110.0, 130.0]
    rows = []
    for R in sample_R:
        if R >= r[-1] - 2.0:
            continue
        Fn = float(np.interp(R, r, F))
        row = {"R": R, "F_numeric": Fn}
        for k in [1, 2, 3, 4]:
            Fa = float(asymptotic_F(R, max_k=k))
            row[f"F_asym_k{k}"] = Fa
            row[f"abs_error_k{k}"] = abs(Fn - Fa)
            row[f"scaled_error_k{k}_times_R{2*k+2}"] = abs(Fn - Fa) * R ** (2*k + 2)
        rows.append(row)
    return rows


def unconstrained_fit(rows: List[Dict[str, float]], min_R: float = 12.0, powers: Tuple[int, ...] = (2,4)) -> Dict[str, float | str | int]:
    xs, ys = [], []
    for row in rows:
        R = row["R_max"]
        if R >= min_R:
            xs.append([1.0] + [R**(-p) for p in powers])
            ys.append(row["C_core"])
    if len(xs) < len(powers) + 1:
        raise ValueError("Not enough rows for unconstrained fit.")
    X = np.asarray(xs, dtype=float)
    y = np.asarray(ys, dtype=float)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    yhat = X @ coef
    C_inf = float(coef[0])
    out: Dict[str, float | str | int] = {
        "fit_model": "C(R)=C_inf+sum A_p/R^p unconstrained",
        "powers": ";".join(str(p) for p in powers),
        "min_R": float(min_R),
        "n_points": int(len(y)),
        "C_inf": C_inf,
        "alpha_inf": 2.0 - C_inf,
        "beta_inf_q0": 1.0 - C_inf,
        "fit_rms": float(np.sqrt(np.mean((y-yhat)**2))),
    }
    for p, c in zip(powers, coef[1:]):
        out[f"A_{p}"] = float(c)
    out["delta_alpha_minus_NLS"] = float(out["alpha_inf"]) - NLS_ALPHA_LEGACY
    out["alpha_minus_phi"] = float(out["alpha_inf"]) - PHI
    return out


def analytic_tail_estimator_stats(rows: List[Dict[str, float]], min_R: float = 12.0, tail_terms: int = 4) -> Dict[str, float | str | int]:
    vals = [row[f"tail_terms_{tail_terms}_Cinf_est"] for row in rows if row["R_max"] >= min_R]
    vals = np.asarray(vals, dtype=float)
    C_inf = float(np.mean(vals))
    std = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
    alpha = 2.0 - C_inf
    return {
        "estimator": f"analytic_tail_terms_{tail_terms}",
        "min_R": float(min_R),
        "n_points": int(len(vals)),
        "C_inf_mean": C_inf,
        "C_inf_std": std,
        "alpha_inf_mean": alpha,
        "alpha_inf_std": std,
        "beta_inf_q0_mean": alpha - 1.0,
        "delta_alpha_minus_NLS": alpha - NLS_ALPHA_LEGACY,
        "alpha_minus_phi": alpha - PHI,
    }


def jackknife_stats(rows: List[Dict[str, float]], min_R: float = 12.0, powers: Tuple[int, ...] = (2,4)) -> Dict[str, float | str | int]:
    selected = [row for row in rows if row["R_max"] >= min_R]
    alphas = []
    for i in range(len(selected)):
        sub = selected[:i] + selected[i+1:]
        if len(sub) >= len(powers)+1:
            alphas.append(float(unconstrained_fit(sub, min_R=min_R, powers=powers)["alpha_inf"]))
    arr = np.asarray(alphas, dtype=float)
    mean = float(np.mean(arr)) if len(arr) else float("nan")
    # conventional jackknife standard error
    se = float(math.sqrt((len(arr)-1)/len(arr) * np.sum((arr-mean)**2))) if len(arr) > 1 else 0.0
    return {
        "fit_model": "jackknife alpha_inf for unconstrained fit",
        "min_R": float(min_R),
        "powers": ";".join(str(p) for p in powers),
        "n_jackknife": int(len(arr)),
        "alpha_jackknife_mean": mean,
        "alpha_jackknife_se": se,
        "delta_alpha_minus_NLS": mean - NLS_ALPHA_LEGACY,
        "alpha_minus_phi": mean - PHI,
    }


def run_v12B0(r_right: float = 160.0, n_init: int = 2200, tol: float = 1.0e-8) -> Dict:
    coeff = EnvelopeCoefficients()
    r, F, Fp, success = solve_envelope_profile(coeff, r_right=r_right, n_init=n_init, tol=tol)
    if not success:
        raise RuntimeError("Envelope BVP solver did not converge.")
    conv = convergence_table(r, F, Fp)
    fval = F_tail_validation_rows(r, F)
    fits = [
        unconstrained_fit(conv, min_R=12.0, powers=(2,4)),
        unconstrained_fit(conv, min_R=20.0, powers=(2,4)),
        unconstrained_fit(conv, min_R=12.0, powers=(2,4,6)),
        unconstrained_fit(conv, min_R=20.0, powers=(2,4,6)),
    ]
    tail_stats = []
    for minR in [8.0, 10.0, 12.0, 15.5, 20.0, 30.0]:
        for terms in [1,2,3,4]:
            tail_stats.append(analytic_tail_estimator_stats(conv, min_R=minR, tail_terms=terms))
    jack = [
        jackknife_stats(conv, min_R=12.0, powers=(2,4)),
        jackknife_stats(conv, min_R=20.0, powers=(2,4)),
        jackknife_stats(conv, min_R=12.0, powers=(2,4,6)),
    ]
    # Principal value: analytic 4-term tail estimator for R>=12.
    principal = analytic_tail_estimator_stats(conv, min_R=12.0, tail_terms=4)
    return {
        "package": "v12B.0",
        "track": "B",
        "success": success,
        "n_nodes_bvp": len(r),
        "r_right": r_right,
        "C1_star": float(F[0]/r[0]),
        "coefficients": asdict(coeff),
        "tail_coefficients": tail_coefficient_rows(),
        "expected_C_fit_coefficients": expected_C_fit_coeff_rows(),
        "convergence": conv,
        "F_tail_validation": fval,
        "unconstrained_fits": fits,
        "analytic_tail_stats": tail_stats,
        "jackknife": jack,
        "principal_estimate": principal,
    }


if __name__ == "__main__":
    import pprint
    pprint.pprint(run_v12B0()["principal_estimate"])
