#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pure-Python backend for SST chi-phase package v5.

v5 is a non-tautological radial profile zoo/admissibility tester.
It computes c_chi^2/v_ref^2 = int rho(x) f(x)^2 x^3 dx / int rho(x) x^3 dx,
where x=r/a, v_theta(r)=v_ref f(x), and rho(x) is an optional relative core-density weight.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Callable, Dict, Iterable, List, Tuple

import numpy as np

EPS = 1.0e-15

@dataclass
class ProfileResult:
    name: str
    family: str
    normalization: str
    params: str
    c_over_v: float
    c2_over_v2: float
    gamma_ratio: float
    slope_boundary: float
    axis_f0: float
    axis_rho0: float
    axis_velocity_regular: bool
    density_core_regular: bool
    boundary_circulation_match: bool
    exterior_slope_match: bool
    finite_weighted_energy: bool
    admissibility_score_4: int
    denom: float
    numer: float
    notes: str

def f_uniform(x: np.ndarray, **kw) -> np.ndarray:
    return np.ones_like(x)

def f_power(x: np.ndarray, p: float = 1.0, **kw) -> np.ndarray:
    return np.power(x, p)

def f_smooth_matched_poly(x: np.ndarray, a0: float = 2.0, **kw) -> np.ndarray:
    return x * (a0 + (3.0 - 2.0 * a0) * x**2 + (a0 - 2.0) * x**4)

def f_regularized_inv_r(x: np.ndarray, eps: float = 0.05, **kw) -> np.ndarray:
    return math.sqrt(1.0 + eps * eps) / np.sqrt(x * x + eps * eps)

def f_lamb_oseen_boundary(x: np.ndarray, sigma: float = 0.35, **kw) -> np.ndarray:
    raw = np.empty_like(x)
    small = np.abs(x) < 1e-10
    raw[~small] = (1.0 - np.exp(-((x[~small] / sigma) ** 2))) / x[~small]
    raw[small] = x[small] / (sigma * sigma)
    raw1 = 1.0 - math.exp(-(1.0 / sigma) ** 2)
    return raw / raw1

def f_phase_inv_r_boundary(x: np.ndarray, **kw) -> np.ndarray:
    return 1.0 / np.maximum(x, EPS)

def f_gaussian_core_max(x: np.ndarray, sigma: float = 0.35, **kw) -> np.ndarray:
    return np.exp(-((x / sigma) ** 2))

def f_gaussian_shell(x: np.ndarray, r0: float = 0.75, sigma: float = 0.12, **kw) -> np.ndarray:
    return np.exp(-0.5 * ((x - r0) / sigma) ** 2)

def rho_const(x: np.ndarray, **kw) -> np.ndarray:
    return np.ones_like(x)

def rho_tanh_core(x: np.ndarray, xi: float = 0.35, **kw) -> np.ndarray:
    return np.tanh(x / xi) ** 2

def rho_pade_core(x: np.ndarray, xi: float = 0.35, **kw) -> np.ndarray:
    return (x * x) / (x * x + xi * xi)

PROFILE_LIBRARY: Dict[str, Tuple[str, Callable, Callable, str, str]] = {
    "uniform_boundary": ("Euler toy", f_uniform, rho_const, "boundary", "constant tangential speed; c/v=1 but axis vector field is not regular"),
    "solid_body_boundary": ("Euler/Rankine core", f_power, rho_const, "boundary", "regular core f=x; expected c/v=sqrt(2/3) for constant density"),
    "smooth_matched_poly": ("regular core + exterior slope match toy", f_smooth_matched_poly, rho_const, "boundary+slope", "regular f(0)=0, f(1)=1, f'(1)=-1; smooth bridge toy"),
    "regularized_inv_r_boundary": ("Euler exterior regularized", f_regularized_inv_r, rho_const, "boundary", "regularized exterior-like 1/r; good slope, poor core regularity"),
    "lamb_oseen_boundary": ("Navier-Stokes/Lamb-Oseen-like", f_lamb_oseen_boundary, rho_const, "boundary", "smooth regular core with circulation-spread parameter sigma, boundary normalized"),
    "nlse_tanh_density_phase": ("NLSE/GP density-regularized phase vortex", f_phase_inv_r_boundary, rho_tanh_core, "boundary phase speed + density core", "singular phase velocity but density vanishes at core; weighted energy finite"),
    "nlse_pade_density_phase": ("NLSE/GP Pade density phase vortex", f_phase_inv_r_boundary, rho_pade_core, "boundary phase speed + Pade density core", "1/r phase velocity with Pade density depletion"),
    "gaussian_core_max": ("localized core toy", f_gaussian_core_max, rho_const, "peak", "peak-normalized central swirl; usually poor boundary circulation"),
    "gaussian_shell": ("shell / boundary-layer toy", f_gaussian_shell, rho_const, "peak shell", "shell-like swirl concentration away from axis"),
}

def _derivative_at_1(f_func: Callable, params: Dict[str, float]) -> float:
    h = 1.0e-5
    y_p = float(f_func(np.array([1.0 + h]), **params)[0])
    y_m = float(f_func(np.array([1.0 - h]), **params)[0])
    return (y_p - y_m) / (2.0 * h)

def _probe(func: Callable, params: Dict[str, float], x0: float = 0.0) -> float:
    try:
        y0 = float(func(np.array([x0]), **params)[0])
        return y0 if math.isfinite(y0) else float("inf")
    except Exception:
        return float("inf")

def integrate_profile(name: str, params: Dict[str, float] | None = None, n: int = 400_000) -> ProfileResult:
    if name not in PROFILE_LIBRARY:
        raise KeyError(f"Unknown profile '{name}'. Known: {sorted(PROFILE_LIBRARY)}")
    family, f_func, rho_func, normalization, notes = PROFILE_LIBRARY[name]
    params = dict(params or {})
    i = np.arange(n, dtype=float)
    x = (i + 0.5) / n
    f = f_func(x, **params)
    rho = rho_func(x, **params)
    weighted = rho * x**3
    denom = float(np.mean(weighted))
    numer = float(np.mean(weighted * f * f))
    c2 = numer / denom if denom > 0 and np.isfinite(numer) else float("nan")
    c = math.sqrt(c2) if c2 >= 0 and math.isfinite(c2) else float("nan")
    f1 = float(f_func(np.array([1.0]), **params)[0])
    slope = _derivative_at_1(f_func, params) / f1 if abs(f1) > 1e-14 else float("nan")
    f0 = _probe(f_func, params)
    rho0 = _probe(rho_func, params)
    axis_velocity_regular = bool(math.isfinite(f0) and abs(f0) < 1e-6)
    density_core_regular = bool(math.isfinite(rho0) and rho0 <= 1e-6)
    boundary_match = bool(math.isfinite(f1) and abs(f1 - 1.0) < 1e-6)
    exterior_match = bool(math.isfinite(slope) and abs(slope + 1.0) < 0.15)
    finite_weighted_energy = bool(math.isfinite(numer) and numer > 0)
    score = int(axis_velocity_regular) + int(boundary_match) + int(exterior_match) + int(finite_weighted_energy)
    return ProfileResult(
        name=name, family=family, normalization=normalization,
        params=",".join(f"{k}={v}" for k, v in sorted(params.items())) or "default",
        c_over_v=c, c2_over_v2=c2, gamma_ratio=f1, slope_boundary=slope,
        axis_f0=f0, axis_rho0=rho0,
        axis_velocity_regular=axis_velocity_regular, density_core_regular=density_core_regular,
        boundary_circulation_match=boundary_match, exterior_slope_match=exterior_match,
        finite_weighted_energy=finite_weighted_energy, admissibility_score_4=score,
        denom=denom, numer=numer, notes=notes)

def default_profile_cases() -> List[Tuple[str, Dict[str, float]]]:
    return [
        ("uniform_boundary", {}),
        ("solid_body_boundary", {"p": 1.0}),
        ("smooth_matched_poly", {"a0": 2.0}),
        ("regularized_inv_r_boundary", {"eps": 0.05}),
        ("lamb_oseen_boundary", {"sigma": 0.35}),
        ("nlse_tanh_density_phase", {"xi": 0.35}),
        ("nlse_pade_density_phase", {"xi": 0.35}),
        ("gaussian_core_max", {"sigma": 0.35}),
        ("gaussian_shell", {"r0": 0.75, "sigma": 0.12}),
    ]

def sweep_cases() -> List[Tuple[str, Dict[str, float]]]:
    cases: List[Tuple[str, Dict[str, float]]] = []
    for p in [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]:
        cases.append(("uniform_boundary", {}) if p == 0.0 else ("solid_body_boundary", {"p": p}))
    for a0 in [1.2, 1.5, 2.0, 2.5]:
        cases.append(("smooth_matched_poly", {"a0": a0}))
    for eps in [0.02, 0.05, 0.1, 0.2]:
        cases.append(("regularized_inv_r_boundary", {"eps": eps}))
    for sigma in [0.2, 0.35, 0.5, 0.75, 1.0]:
        cases.append(("lamb_oseen_boundary", {"sigma": sigma}))
    for xi in [0.15, 0.25, 0.35, 0.5, 0.75]:
        cases.append(("nlse_tanh_density_phase", {"xi": xi}))
        cases.append(("nlse_pade_density_phase", {"xi": xi}))
    for sigma in [0.2, 0.35, 0.5, 0.75]:
        cases.append(("gaussian_core_max", {"sigma": sigma}))
    return cases

def evaluate_cases(cases: Iterable[Tuple[str, Dict[str, float]]], n: int = 400_000) -> List[ProfileResult]:
    return [integrate_profile(name, params, n=n) for name, params in cases]

def profile_curve(name: str, params: Dict[str, float] | None = None, n: int = 1000):
    if name not in PROFILE_LIBRARY:
        raise KeyError(name)
    _, f_func, rho_func, _, _ = PROFILE_LIBRARY[name]
    params = dict(params or {})
    x = np.linspace(0.0, 1.0, n)
    x_eval = np.maximum(x, 1e-6)
    return x, f_func(x_eval, **params), rho_func(x, **params)

def result_to_dict(result: ProfileResult) -> Dict[str, object]:
    return asdict(result)
