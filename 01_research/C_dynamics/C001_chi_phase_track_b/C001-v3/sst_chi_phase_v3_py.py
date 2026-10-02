"""Pure-Python fallback for SST chi-phase v3.

v3 is deliberately non-tautological: it does NOT set
K_chi = rho_f * v_swirl**2 * J.  Instead it extracts K_chi from a
resolved radial swirl profile v_theta(r):

    I_chi = rho_f * ∫_A r_perp^2 dA
    K_chi = rho_f * ∫_A v_theta(r)^2 r_perp^2 dA
    c_chi = sqrt(K_chi / I_chi)

Thus c_chi/v_ref can differ from 1.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

PI = math.pi


def _get(params: Dict[str, float], name: str, default: float) -> float:
    try:
        return float(params.get(name, default))
    except Exception:
        return default


def raw_profile(profile: str, x: float, params: Dict[str, float] | None = None) -> float:
    """Dimensionless raw v_theta/v_ref profile before normalization."""
    params = params or {}
    p = profile.lower().strip()
    x = max(0.0, min(1.0, float(x)))

    if p in {"uniform", "constant", "shell"}:
        return 1.0

    if p in {"solid", "solid_body", "solid-body", "rankine_inside"}:
        return x

    if p in {"quadratic", "quadratic_core", "parabolic_edge"}:
        # Smooth monotone profile, zero at center and one at boundary.
        return x * (2.0 - x)

    if p in {"irrotational", "irrotational_reg", "vortex_1_over_r"}:
        eps = max(_get(params, "eps", 0.05), 1e-9)
        return 1.0 / max(x, eps)

    if p in {"rankine", "rankine_vortex"}:
        core = min(max(_get(params, "core", 0.35), 1e-9), 1.0)
        if x <= core:
            return x / core
        return core / max(x, 1e-12)

    if p in {"lamb_oseen", "oseen"}:
        # Raw profile proportional to (1-exp(-(r/sigma)^2))/r.
        sigma = max(_get(params, "sigma", 0.35), 1e-9)
        if x < 1e-9:
            return 0.0
        return (1.0 - math.exp(-(x / sigma) ** 2)) / x

    if p in {"gaussian_core", "gaussian"}:
        sigma = max(_get(params, "sigma", 0.35), 1e-9)
        return math.exp(-0.5 * (x / sigma) ** 2)

    if p in {"gaussian_shell", "shell_gaussian"}:
        r0 = min(max(_get(params, "r0", 0.75), 0.0), 1.0)
        sigma = max(_get(params, "sigma", 0.12), 1e-9)
        return math.exp(-0.5 * ((x - r0) / sigma) ** 2)

    raise ValueError(f"unknown profile: {profile}")


def integrate_profile_raw(profile: str, params: Dict[str, float] | None = None, n_radial: int = 200000) -> Dict[str, float]:
    """Integrate raw profile moments on the unit disk using midpoint rule."""
    params = params or {}
    n = int(max(64, n_radial))
    dx = 1.0 / n
    j = 0.0
    k_raw = 0.0
    max_abs = 0.0
    for i in range(n):
        x = (i + 0.5) * dx
        f = raw_profile(profile, x, params)
        weight = x ** 3
        j += weight * dx
        k_raw += f * f * weight * dx
        max_abs = max(max_abs, abs(f))
    # boundary sample not midpoint; use x=1.
    f_boundary = raw_profile(profile, 1.0, params)
    return {
        "j_dimless_radial": j,
        "k_dimless_raw_radial": k_raw,
        "raw_rms_r2": math.sqrt(k_raw / j),
        "raw_boundary": f_boundary,
        "raw_max_abs": max_abs,
    }


def normalization_scale(profile: str, normalization: str, params: Dict[str, float] | None = None, n_radial: int = 200000) -> float:
    normalization = normalization.lower().strip()
    info = integrate_profile_raw(profile, params, n_radial=n_radial)
    if normalization in {"boundary", "edge"}:
        denom = info["raw_boundary"]
    elif normalization in {"max", "peak"}:
        denom = info["raw_max_abs"]
    elif normalization in {"rms_r2", "r2_rms", "weighted_rms"}:
        # This is intentionally labelled as calibration, because it forces c/v_ref=1.
        denom = info["raw_rms_r2"]
    elif normalization in {"none", "raw"}:
        denom = 1.0
    else:
        raise ValueError(f"unknown normalization: {normalization}")
    if abs(denom) < 1e-300:
        raise ValueError(f"normalization denominator too small for {profile}/{normalization}")
    return 1.0 / denom


def profile_metrics(
    profile: str,
    a_core: float,
    rho_f: float,
    v_ref: float,
    normalization: str = "boundary",
    params: Dict[str, float] | None = None,
    n_radial: int = 200000,
) -> Dict[str, float | str]:
    """Compute I_chi, K_chi and c_chi from an actual v_theta(r) profile."""
    params = params or {}
    a = float(a_core)
    rho = float(rho_f)
    v = float(v_ref)
    if a <= 0 or rho <= 0 or v <= 0:
        raise ValueError("a_core, rho_f and v_ref must be positive")

    raw = integrate_profile_raw(profile, params, n_radial=n_radial)
    scale = normalization_scale(profile, normalization, params, n_radial=n_radial)

    # Unit-disk radial integrals multiplied by 2*pi*a^4.
    J = 2.0 * PI * (a ** 4) * raw["j_dimless_radial"]
    Kgeom = 2.0 * PI * (a ** 4) * (scale ** 2) * raw["k_dimless_raw_radial"]

    I = rho * J
    K = rho * (v ** 2) * Kgeom
    c = math.sqrt(K / I)

    # Analytic J for full circular disk.
    J_analytic = 0.5 * PI * a ** 4
    j_rel_error = J / J_analytic - 1.0

    return {
        "profile": profile,
        "normalization": normalization,
        "a_core": a,
        "rho_f": rho,
        "v_ref": v,
        "I_chi": I,
        "K_chi": K,
        "J_numeric": J,
        "J_analytic_disk": J_analytic,
        "J_rel_error": j_rel_error,
        "Kgeom_over_J": Kgeom / J,
        "c_chi": c,
        "c_over_v_ref": c / v,
        "scale": scale,
        "raw_boundary": raw["raw_boundary"],
        "raw_max_abs": raw["raw_max_abs"],
        "raw_rms_r2": raw["raw_rms_r2"],
        "n_radial": int(n_radial),
    }


def profile_sweep(
    profiles: Iterable[Tuple[str, str, Dict[str, float]]],
    a_core: float,
    rho_f: float,
    v_ref: float,
    n_radial: int = 200000,
) -> List[Dict[str, float | str]]:
    return [
        profile_metrics(name, a_core, rho_f, v_ref, norm, params, n_radial=n_radial)
        for name, norm, params in profiles
    ]


def horn_loop_frequency_ratios(c_over_v: float, n_max: int = 16, n_grid: int = 4096) -> List[Dict[str, float]]:
    """Discrete central-difference spectrum on L=2*pi*r_c.

    If c/v_ref != 1, omega_n/(n*omega_c) tends to c/v_ref.
    Finite-difference dispersion multiplies by sin(pi*n/N)/(pi*n/N).
    """
    rows = []
    for n in range(1, int(n_max) + 1):
        x = PI * n / int(n_grid)
        fd = math.sin(x) / x
        rows.append({
            "n": n,
            "continuous_ratio": float(c_over_v),
            "fd_ratio": float(c_over_v) * fd,
            "fd_relative_error_vs_cont": fd - 1.0,
        })
    return rows


def spectrum_convergence(c_over_v: float = 1.0, n_max: int = 32, grids: Iterable[int] = (128,256,512,1024,2048,4096,8192)) -> List[Dict[str, float]]:
    rows = []
    for N in grids:
        max_err = 0.0
        pred = 0.0
        for n in range(1, n_max + 1):
            x = PI * n / N
            fd = math.sin(x) / x
            err = abs(fd - 1.0)
            max_err = max(max_err, err)
        x_max = PI * n_max / N
        pred = abs(math.sin(x_max)/x_max - 1.0)
        rows.append({"N": int(N), "max_rel_error": max_err, "prediction": pred, "c_over_v": c_over_v})
    return rows
