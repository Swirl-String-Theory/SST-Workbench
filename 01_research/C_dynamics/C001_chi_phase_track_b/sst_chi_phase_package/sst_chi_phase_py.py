"""Pure-Python fallback for sst_chi_phase.cpp.

Used automatically when pybind11 is unavailable. API-compatible with the small
subset used by simulate_chi_phase.py.
"""

from __future__ import annotations

import math

PI = math.pi


def _require_positive(x: float, name: str):
    if not (x > 0.0) or not math.isfinite(x):
        raise ValueError(f"{name} must be positive and finite")


def transverse_moment_circular_analytic(a_core: float) -> float:
    _require_positive(a_core, "a_core")
    return 0.5 * PI * a_core**4


def transverse_moment_circular_quadrature(a_core: float, n_r: int, n_theta: int) -> float:
    _require_positive(a_core, "a_core")
    if n_r <= 0 or n_theta <= 0:
        raise ValueError("n_r and n_theta must be positive")
    dr = a_core / n_r
    dtheta = 2.0 * PI / n_theta
    moment = 0.0
    for ir in range(n_r):
        r = (ir + 0.5) * dr
        shell = r**3 * dr * dtheta
        moment += n_theta * shell
    return moment


def compute_chi_constants(rho_f: float, v_swirl: float, a_core: float, n_r: int, n_theta: int):
    _require_positive(rho_f, "rho_f")
    _require_positive(v_swirl, "v_swirl")
    _require_positive(a_core, "a_core")
    j_analytic = transverse_moment_circular_analytic(a_core)
    j_numeric = transverse_moment_circular_quadrature(a_core, n_r, n_theta)
    i_analytic = rho_f * j_analytic
    k_analytic = rho_f * v_swirl**2 * j_analytic
    c_analytic = math.sqrt(k_analytic / i_analytic)
    i_numeric = rho_f * j_numeric
    k_numeric = rho_f * v_swirl**2 * j_numeric
    c_numeric = math.sqrt(k_numeric / i_numeric)
    return {
        "a_core": a_core,
        "J_analytic": j_analytic,
        "J_numeric": j_numeric,
        "J_rel_error": (j_numeric - j_analytic) / j_analytic,
        "I_chi_analytic": i_analytic,
        "K_chi_analytic": k_analytic,
        "c_chi_analytic": c_analytic,
        "c_chi_over_v_analytic": c_analytic / v_swirl,
        "I_chi_numeric": i_numeric,
        "K_chi_numeric": k_numeric,
        "c_chi_numeric": c_numeric,
        "c_chi_over_v_numeric": c_numeric / v_swirl,
    }


def continuous_phase_spectrum(v_swirl: float, L_chi: float, n_max: int, omega_gap: float):
    _require_positive(v_swirl, "v_swirl")
    _require_positive(L_chi, "L_chi")
    if n_max <= 0:
        raise ValueError("n_max must be positive")
    if omega_gap < 0.0 or not math.isfinite(omega_gap):
        raise ValueError("omega_gap must be non-negative and finite")
    return [
        math.sqrt(omega_gap**2 + v_swirl**2 * (2.0 * PI * n / L_chi) ** 2)
        for n in range(1, n_max + 1)
    ]


def discrete_phase_spectrum(v_swirl: float, L_chi: float, n_grid: int, n_max: int, omega_gap: float):
    _require_positive(v_swirl, "v_swirl")
    _require_positive(L_chi, "L_chi")
    if n_grid < 8:
        raise ValueError("n_grid must be at least 8")
    if n_max <= 0 or n_max >= n_grid // 2:
        raise ValueError("n_max must be in [1, n_grid/2)")
    if omega_gap < 0.0 or not math.isfinite(omega_gap):
        raise ValueError("omega_gap must be non-negative and finite")
    ds = L_chi / n_grid
    out = []
    for n in range(1, n_max + 1):
        k_eff = (2.0 / ds) * math.sin(PI * n / n_grid)
        out.append(math.sqrt(omega_gap**2 + v_swirl**2 * k_eff**2))
    return out
