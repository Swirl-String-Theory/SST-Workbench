"""Pure-Python fallback for SST chi-phase v4.

v4 tests four explicit radial core profiles with independent profile-derived
stiffness and admissibility diagnostics:

    I_chi = rho_f * ∫_A r_perp^2 dA
    K_chi = rho_f * ∫_A v_theta(r)^2 r_perp^2 dA
    c_chi^2 = K_chi / I_chi

The package does not set K_chi = rho_f*v_ref^2*J.  It extracts K_chi from
v_theta(r), then checks circulation, energy, axis regularity, boundary matching,
exterior 1/r slope matching, and the r^2-RMS condition.
"""
from __future__ import annotations

import math
from typing import Dict, Iterable, List, Tuple

PI = math.pi


def _get(params: Dict[str, float] | None, name: str, default: float) -> float:
    try:
        return float((params or {}).get(name, default))
    except Exception:
        return default


def raw_profile(profile: str, x: float, params: Dict[str, float] | None = None) -> float:
    """Dimensionless raw v_theta/v_ref on x=r/a in [0,1]."""
    p = profile.lower().strip()
    x = max(0.0, min(1.0, float(x)))
    params = params or {}

    if p in {"uniform", "uniform_boundary", "constant_shell"}:
        return 1.0

    if p in {"solid_body", "solid-body", "solid"}:
        return x

    if p in {"irrotational_reg", "regularized_1_over_r", "vortex_1_over_r"}:
        eps = max(_get(params, "eps", 0.05), 1e-12)
        return 1.0 / math.sqrt(x*x + eps*eps)

    if p in {"gaussian_core", "gaussian"}:
        sigma = max(_get(params, "sigma", 0.35), 1e-12)
        return math.exp(-0.5 * (x / sigma) ** 2)

    if p in {"rankine_matched", "rankine"}:
        core = min(max(_get(params, "core", 0.35), 1e-12), 1.0)
        if x <= core:
            return x / core
        return core / max(x, 1e-12)

    raise ValueError(f"unknown profile: {profile}")


def profile_derivative(profile: str, x: float, params: Dict[str, float] | None = None) -> float:
    """Derivative df/dx of raw profile at x. Used for boundary slope diagnostics."""
    p = profile.lower().strip()
    x = max(0.0, min(1.0, float(x)))
    params = params or {}

    if p in {"uniform", "uniform_boundary", "constant_shell"}:
        return 0.0

    if p in {"solid_body", "solid-body", "solid"}:
        return 1.0

    if p in {"irrotational_reg", "regularized_1_over_r", "vortex_1_over_r"}:
        eps = max(_get(params, "eps", 0.05), 1e-12)
        return -x / ((x*x + eps*eps) ** 1.5)

    if p in {"gaussian_core", "gaussian"}:
        sigma = max(_get(params, "sigma", 0.35), 1e-12)
        return raw_profile(profile, x, params) * (-(x / (sigma*sigma)))

    if p in {"rankine_matched", "rankine"}:
        core = min(max(_get(params, "core", 0.35), 1e-12), 1.0)
        if x < core:
            return 1.0 / core
        return -core / max(x*x, 1e-24)

    raise ValueError(f"unknown profile: {profile}")


def raw_info(profile: str, params: Dict[str, float] | None = None, n_radial: int = 200000) -> Dict[str, float]:
    """Midpoint-rule integrals on unit disk.

    J_radial = ∫_0^1 x^3 dx = 1/4
    K_radial = ∫_0^1 f(x)^2 x^3 dx
    E_radial = ∫_0^1 f(x)^2 x dx
    """
    n = int(max(128, n_radial))
    dx = 1.0 / n
    J = 0.0
    K = 0.0
    E = 0.0
    max_abs = 0.0
    for i in range(n):
        x = (i + 0.5) * dx
        f = raw_profile(profile, x, params)
        f2 = f * f
        J += x**3 * dx
        K += f2 * x**3 * dx
        E += f2 * x * dx
        max_abs = max(max_abs, abs(f))
    boundary = raw_profile(profile, 1.0, params)
    center = raw_profile(profile, 0.0, params)
    dboundary = profile_derivative(profile, 1.0, params)
    return {
        "J_radial": J,
        "K_radial_raw": K,
        "E_radial_raw": E,
        "raw_boundary": boundary,
        "raw_center": center,
        "raw_max_abs": max_abs,
        "raw_r2_rms": math.sqrt(K / J),
        "raw_energy_rms": math.sqrt(2.0 * E),  # area RMS on unit disk
        "raw_boundary_derivative": dboundary,
    }


def normalization_scale(profile: str, normalization: str, params: Dict[str, float] | None = None, n_radial: int = 200000) -> float:
    norm = normalization.lower().strip()
    info = raw_info(profile, params, n_radial)
    if norm in {"boundary", "edge"}:
        denom = info["raw_boundary"]
    elif norm in {"max", "peak"}:
        denom = info["raw_max_abs"]
    elif norm in {"rms_r2", "r2_rms", "weighted_rms"}:
        denom = info["raw_r2_rms"]
    elif norm in {"none", "raw"}:
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
) -> Dict[str, float | str | int]:
    params = params or {}
    a = float(a_core)
    rho = float(rho_f)
    v = float(v_ref)
    if a <= 0 or rho <= 0 or v <= 0:
        raise ValueError("a_core, rho_f and v_ref must be positive")

    info = raw_info(profile, params, n_radial)
    scale = normalization_scale(profile, normalization, params, n_radial)

    # Dimensional integrals on a disk: dA = 2*pi*r dr = 2*pi*a^2*x dx.
    J = 2.0 * PI * a**4 * info["J_radial"]
    Kgeom = 2.0 * PI * a**4 * scale**2 * info["K_radial_raw"]
    Egeom = 2.0 * PI * a**2 * scale**2 * info["E_radial_raw"]

    I = rho * J
    K_chi = rho * v**2 * Kgeom
    c = math.sqrt(K_chi / I)
    energy_per_length = 0.5 * rho * v**2 * Egeom

    boundary_over_v = scale * info["raw_boundary"]
    center_over_v = scale * info["raw_center"]
    max_over_v = scale * info["raw_max_abs"]
    boundary_slope_scaled = scale * info["raw_boundary_derivative"]
    boundary_log_slope = boundary_slope_scaled / boundary_over_v if abs(boundary_over_v) > 1e-300 else float("nan")

    gamma_boundary = 2.0 * PI * a * v * boundary_over_v
    gamma_ref = 2.0 * PI * a * v

    J_analytic = 0.5 * PI * a**4

    # Admissibility diagnostics. These are not pass/fail truth; they document which physical constraints each profile meets.
    axis_regular_tol = 1e-3
    boundary_tol = 1e-6
    slope_tol = 5e-2
    finite_tol = 1e100
    axis_regular = int(abs(center_over_v) < axis_regular_tol)
    boundary_matches = int(abs(boundary_over_v - 1.0) < boundary_tol)
    exterior_slope_matches = int(abs(boundary_log_slope + 1.0) < slope_tol)
    finite_energy = int(math.isfinite(energy_per_length) and abs(energy_per_length) < finite_tol)
    r2_rms_matches_ref = int(abs(c / v - 1.0) < 1e-6)
    calibration_mode = int(normalization.lower().strip() in {"rms_r2", "r2_rms", "weighted_rms"})

    # Simple score to rank profiles for core admissibility; calibration does not add points.
    score = axis_regular + boundary_matches + exterior_slope_matches + finite_energy

    return {
        "profile": profile,
        "normalization": normalization,
        "a_core": a,
        "rho_f": rho,
        "v_ref": v,
        "scale": scale,
        "I_chi": I,
        "K_chi": K_chi,
        "c_chi": c,
        "c_over_v_ref": c / v,
        "J_numeric": J,
        "J_analytic_disk": J_analytic,
        "J_rel_error": J / J_analytic - 1.0,
        "Kgeom": Kgeom,
        "Kgeom_over_J": Kgeom / J,
        "Egeom": Egeom,
        "energy_per_length": energy_per_length,
        "gamma_boundary": gamma_boundary,
        "gamma_ref": gamma_ref,
        "gamma_boundary_over_ref": gamma_boundary / gamma_ref,
        "boundary_over_v": boundary_over_v,
        "center_over_v": center_over_v,
        "max_over_v": max_over_v,
        "boundary_log_slope": boundary_log_slope,
        "axis_regular": axis_regular,
        "boundary_matches": boundary_matches,
        "exterior_slope_matches": exterior_slope_matches,
        "finite_energy": finite_energy,
        "r2_rms_matches_ref": r2_rms_matches_ref,
        "calibration_mode": calibration_mode,
        "admissibility_score": score,
        "n_radial": int(n_radial),
    }


def default_four_profiles() -> List[Tuple[str, str, Dict[str, float], str]]:
    return [
        ("uniform", "boundary", {}, "uniform boundary"),
        ("solid_body", "boundary", {}, "solid-body boundary"),
        ("irrotational_reg", "boundary", {"eps": 0.05}, "regularized 1/r boundary, eps=0.05"),
        ("gaussian_core", "max", {"sigma": 0.35}, "Gaussian core max, sigma=0.35"),
    ]


def extended_profiles() -> List[Tuple[str, str, Dict[str, float], str]]:
    rows = default_four_profiles()
    rows += [
        ("rankine_matched", "boundary", {"core": 0.35}, "Rankine matched boundary, core=0.35"),
        ("solid_body", "rms_r2", {}, "solid-body r2-RMS calibration (forces c/v=1)"),
    ]
    return rows


def horn_loop_frequency_ratios(c_over_v: float, n_max: int = 32, n_grid: int = 4096) -> List[Dict[str, float]]:
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


def spectrum_convergence(c_over_v: float = 1.0, n_max: int = 32, grids: Iterable[int] = (128, 256, 512, 1024, 2048, 4096, 8192)) -> List[Dict[str, float]]:
    rows = []
    for N in grids:
        max_err = 0.0
        for n in range(1, int(n_max) + 1):
            x = PI * n / int(N)
            fd = math.sin(x) / x
            max_err = max(max_err, abs(fd - 1.0))
        x_max = PI * int(n_max) / int(N)
        pred = abs(math.sin(x_max) / x_max - 1.0)
        rows.append({"N": int(N), "max_rel_error": max_err, "prediction": pred, "c_over_v": c_over_v})
    return rows
