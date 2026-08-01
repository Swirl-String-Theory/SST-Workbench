"""Pure-Python fallback for sst_chi_phase_v2.cpp.

The fallback is API-compatible with the subset used by simulate_chi_phase_v2.py.
It is slower than the pybind11 kernel but fully self-contained.
"""

from __future__ import annotations

import math

PI = math.pi


def _require_positive(x: float, name: str):
    if not (x > 0.0) or not math.isfinite(x):
        raise ValueError(f"{name} must be positive and finite")


def _require_nonnegative(x: float, name: str):
    if x < 0.0 or not math.isfinite(x):
        raise ValueError(f"{name} must be non-negative and finite")


def _require_quadrature(n_r: int, n_theta: int):
    if n_r <= 0 or n_theta <= 0:
        raise ValueError("n_r and n_theta must be positive")


def constants_from_moment(rho_f: float, v_swirl: float, J: float):
    _require_positive(rho_f, "rho_f")
    _require_positive(v_swirl, "v_swirl")
    _require_positive(J, "J")
    I = rho_f * J
    K = rho_f * v_swirl**2 * J
    c = math.sqrt(K / I)
    return {"J": J, "I_chi": I, "K_chi": K, "c_chi": c, "c_chi_over_v": c / v_swirl}


def moment_circle_analytic(a: float) -> float:
    _require_positive(a, "a")
    return 0.5 * PI * a**4


def moment_annulus_analytic(a_inner: float, a_outer: float) -> float:
    _require_nonnegative(a_inner, "a_inner")
    _require_positive(a_outer, "a_outer")
    if not (a_inner < a_outer):
        raise ValueError("a_inner must be smaller than a_outer")
    return 0.5 * PI * (a_outer**4 - a_inner**4)


def moment_ellipse_analytic(a: float, b: float) -> float:
    _require_positive(a, "a")
    _require_positive(b, "b")
    return 0.25 * PI * a * b * (a**2 + b**2)


def ellipse_tensor_analytic(a: float, b: float):
    _require_positive(a, "a")
    _require_positive(b, "b")
    return {
        "M_xx": 0.25 * PI * a**3 * b,
        "M_yy": 0.25 * PI * a * b**3,
        "M_xy": 0.0,
        "J_trace": moment_ellipse_analytic(a, b),
    }


def moment_circle_quadrature(a: float, n_r: int, n_theta: int) -> float:
    _require_positive(a, "a")
    _require_quadrature(n_r, n_theta)
    dr = a / n_r
    dtheta = 2.0 * PI / n_theta
    moment = 0.0
    for ir in range(n_r):
        r = (ir + 0.5) * dr
        shell = r**3 * dr * dtheta
        moment += n_theta * shell
    return moment


def moment_annulus_quadrature(a_inner: float, a_outer: float, n_r: int, n_theta: int) -> float:
    _require_nonnegative(a_inner, "a_inner")
    _require_positive(a_outer, "a_outer")
    if not (a_inner < a_outer):
        raise ValueError("a_inner must be smaller than a_outer")
    _require_quadrature(n_r, n_theta)
    dr = (a_outer - a_inner) / n_r
    dtheta = 2.0 * PI / n_theta
    moment = 0.0
    for ir in range(n_r):
        r = a_inner + (ir + 0.5) * dr
        shell = r**3 * dr * dtheta
        moment += n_theta * shell
    return moment


def moment_ellipse_quadrature(a: float, b: float, n_r: int, n_theta: int) -> float:
    _require_positive(a, "a")
    _require_positive(b, "b")
    _require_quadrature(n_r, n_theta)
    dr = 1.0 / n_r
    dtheta = 2.0 * PI / n_theta
    moment = 0.0
    for ir in range(n_r):
        r = (ir + 0.5) * dr
        for it in range(n_theta):
            th = (it + 0.5) * dtheta
            x = a * r * math.cos(th)
            y = b * r * math.sin(th)
            jac = a * b * r
            moment += (x * x + y * y) * jac * dr * dtheta
    return moment


def ellipse_tensor_quadrature(a: float, b: float, n_r: int, n_theta: int):
    _require_positive(a, "a")
    _require_positive(b, "b")
    _require_quadrature(n_r, n_theta)
    dr = 1.0 / n_r
    dtheta = 2.0 * PI / n_theta
    mxx = myy = mxy = 0.0
    for ir in range(n_r):
        r = (ir + 0.5) * dr
        for it in range(n_theta):
            th = (it + 0.5) * dtheta
            x = a * r * math.cos(th)
            y = b * r * math.sin(th)
            weight = a * b * r * dr * dtheta
            mxx += x * x * weight
            myy += y * y * weight
            mxy += x * y * weight
    return {"M_xx": mxx, "M_yy": myy, "M_xy": mxy, "J_trace": mxx + myy}


def compute_chi_from_shape(shape: str, rho_f: float, v_swirl: float, p1: float, p2: float, n_r: int, n_theta: int):
    _require_positive(rho_f, "rho_f")
    _require_positive(v_swirl, "v_swirl")
    if shape == "circle":
        j_analytic = moment_circle_analytic(p1)
        j_numeric = moment_circle_quadrature(p1, n_r, n_theta)
    elif shape == "annulus":
        j_analytic = moment_annulus_analytic(p1, p2)
        j_numeric = moment_annulus_quadrature(p1, p2, n_r, n_theta)
    elif shape == "ellipse":
        j_analytic = moment_ellipse_analytic(p1, p2)
        j_numeric = moment_ellipse_quadrature(p1, p2, n_r, n_theta)
    else:
        raise ValueError("Unknown shape. Use circle, annulus, or ellipse")

    i_analytic = rho_f * j_analytic
    k_analytic = rho_f * v_swirl**2 * j_analytic
    c_analytic = math.sqrt(k_analytic / i_analytic)
    i_numeric = rho_f * j_numeric
    k_numeric = rho_f * v_swirl**2 * j_numeric
    c_numeric = math.sqrt(k_numeric / i_numeric)
    return {
        "shape": shape,
        "p1": p1,
        "p2": p2,
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


def anisotropic_ellipse_speed_check(rho_f: float, v_swirl: float, a: float, b: float):
    mt = ellipse_tensor_analytic(a, b)
    mxx = mt["M_xx"]
    myy = mt["M_yy"]
    c_x_shared = math.sqrt((rho_f * v_swirl**2 * mxx) / (rho_f * mxx))
    c_y_shared = math.sqrt((rho_f * v_swirl**2 * myy) / (rho_f * myy))
    m_mean = 0.5 * (mxx + myy)
    c_x_counter = math.sqrt((rho_f * v_swirl**2 * m_mean) / (rho_f * mxx))
    c_y_counter = math.sqrt((rho_f * v_swirl**2 * m_mean) / (rho_f * myy))
    return {
        "a": a,
        "b": b,
        "aspect_b_over_a": b / a,
        "M_xx": mxx,
        "M_yy": myy,
        "canonical_cx_over_v": c_x_shared / v_swirl,
        "canonical_cy_over_v": c_y_shared / v_swirl,
        "counterfactual_cx_over_v": c_x_counter / v_swirl,
        "counterfactual_cy_over_v": c_y_counter / v_swirl,
        "counterfactual_split_abs": abs(c_x_counter - c_y_counter) / v_swirl,
    }


def continuous_phase_spectrum(v_swirl: float, L_chi: float, n_max: int, omega_gap: float):
    _require_positive(v_swirl, "v_swirl")
    _require_positive(L_chi, "L_chi")
    if n_max <= 0:
        raise ValueError("n_max must be positive")
    _require_nonnegative(omega_gap, "omega_gap")
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
    _require_nonnegative(omega_gap, "omega_gap")
    ds = L_chi / n_grid
    out = []
    for n in range(1, n_max + 1):
        k_eff = (2.0 / ds) * math.sin(PI * n / n_grid)
        out.append(math.sqrt(omega_gap**2 + v_swirl**2 * k_eff**2))
    return out


def spectrum_error_summary(v_swirl: float, L_chi: float, n_grid: int, n_max: int, omega_gap: float):
    cont = continuous_phase_spectrum(v_swirl, L_chi, n_max, omega_gap)
    disc = discrete_phase_spectrum(v_swirl, L_chi, n_grid, n_max, omega_gap)
    max_abs_rel = max(abs(d / c - 1.0) for c, d in zip(cont, disc))
    return {
        "n_grid": n_grid,
        "n_max": n_max,
        "omega1_ratio_disc_over_cont": disc[0] / cont[0],
        "max_abs_rel_error": max_abs_rel,
    }
