from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from . import _config
from .constants import (
    C,
    GAMMA_CANON,
    J1738_ALPHA1_LOWER_68,
    J1738_ALPHA1_LOWER_90,
    J1738_PDOT_GAL,
    J1738_PDOT_GAL_SIGMA,
    J1738_PDOT_OBS,
    J1738_PDOT_OBS_SIGMA,
    J1738_PDOT_SHK,
    J1738_PDOT_SHK_SIGMA,
    R_C,
    RHO_F,
    SOLAR_SYSTEM_ALPHA1_ABS,
    SOLAR_SYSTEM_ALPHA2_ABS,
    V_SWIRL_OVER_C_SQ,
)

_BACKEND = None
_BACKEND_NAME = None


def write_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        p.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    seen = set()
    for row in rows:
        for k in row:
            if k not in seen:
                seen.add(k); fields.append(k)
    with p.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


def _load_backend(force_python: bool = False, force_build: bool = False, build_verbose: bool = False):
    global _BACKEND, _BACKEND_NAME
    if force_python:
        from . import fallback
        return fallback, "python"
    if _BACKEND is not None:
        return _BACKEND, _BACKEND_NAME
    try:
        from .build_ext_if_needed import build_if_needed
        build_if_needed(force=force_build, verbose=build_verbose)
        mod = __import__(f"{_config.PACKAGE_NAME}.{_config.EXT_BASENAME}", fromlist=["*"])
        _BACKEND, _BACKEND_NAME = mod, "cpp"
    except Exception:
        from . import fallback
        _BACKEND, _BACKEND_NAME = fallback, "python"
    return _BACKEND, _BACKEND_NAME


def backend_name(force_python: bool = False) -> str:
    return _load_backend(force_python=force_python)[1]


def filament_energy(points, rho: float = RHO_F, gamma: float = GAMMA_CANON,
                    core_radius: float = R_C, *, force_python: bool = False) -> float:
    backend, _ = _load_backend(force_python=force_python)
    return float(backend.filament_energy(np.asarray(points, dtype=float), float(rho), float(gamma), float(core_radius)))


def biot_savart_velocity(points, gamma: float = GAMMA_CANON, core_radius: float = R_C,
                         background=(0.0, 0.0, 0.0), *, force_python: bool = False) -> np.ndarray:
    backend, _ = _load_backend(force_python=force_python)
    return np.asarray(backend.biot_savart_velocity(np.asarray(points, dtype=float), float(gamma),
                                                   float(core_radius), np.asarray(background, dtype=float)), dtype=float)


def torus_knot(n: int = 96, p: int = 2, q: int = 3,
               major_radius: float = 4.0 * R_C, minor_radius: float = 1.5 * R_C) -> np.ndarray:
    """Simple torus-knot seed, not an ideal-knot solution."""
    t = np.linspace(0.0, 2.0 * math.pi, int(n), endpoint=False)
    R = major_radius + minor_radius * np.cos(q * t)
    return np.column_stack([R * np.cos(p * t), R * np.sin(p * t), minor_radius * np.sin(q * t)])


def _shape_signature(points: np.ndarray) -> np.ndarray:
    p = np.asarray(points, dtype=float)
    c = p.mean(axis=0)
    x = p - c
    # Translation-invariant, rotation-covariant quadratic size signature.
    cov = (x.T @ x) / len(x)
    eig = np.linalg.eigvalsh(cov)
    return np.sort(eig)


def evolve_filament(points: np.ndarray, *, dt: float, steps: int, background,
                    gamma: float = GAMMA_CANON, core_radius: float = R_C,
                    force_python: bool = False) -> np.ndarray:
    """RK2 evolution of a desingularized filament plus uniform background flow."""
    p = np.asarray(points, dtype=float).copy()
    bg = np.asarray(background, dtype=float)
    for _ in range(int(steps)):
        k1 = biot_savart_velocity(p, gamma, core_radius, bg, force_python=force_python)
        mid = p + 0.5 * dt * k1
        k2 = biot_savart_velocity(mid, gamma, core_radius, bg, force_python=force_python)
        p = p + dt * k2
    return p


def fit_drift_sensitivity(rows: list[dict[str, Any]]) -> dict[str, float]:
    """Fit dE/E = chi0 beta^2 + chi2[(beta.a)^2-beta^2/3] + intercept."""
    X, y = [], []
    for r in rows:
        beta2 = float(r["beta2"])
        mu2 = float(r["axis_projection_sq"])
        X.append([1.0, beta2, mu2 - beta2 / 3.0])
        y.append(float(r["delta_E_over_E0"]))
    coef, *_ = np.linalg.lstsq(np.asarray(X), np.asarray(y), rcond=None)
    yhat = np.asarray(X) @ coef
    resid = np.asarray(y) - yhat
    return {
        "intercept": float(coef[0]),
        "chi0": float(coef[1]),
        "chi2": float(coef[2]),
        "rms_residual": float(np.sqrt(np.mean(resid**2))),
    }


def drift_scan(*, n: int = 72, beta_values: Iterable[float] = (0.0, 5e-4, 1e-3, 2e-3, 0.00364867628),
               steps: int = 2, dt_factor: float = 0.01, points: np.ndarray | None = None,
               force_python: bool = False, inject_chi0: float = 0.0, inject_chi2: float = 0.0) -> dict[str, Any]:
    """
    Galilean-drift baseline test.

    A uniform background velocity is added to the incompressible Euler filament dynamics.
    Because pure Euler is Galilean invariant, translation-reduced intrinsic energy/shape should
    be independent of that drift. Nonzero fitted sensitivity beyond numerical error falsifies
    this baseline implementation (or signals extra, non-Euler SST constitutive physics).
    """
    p0 = torus_knot(n=n) if points is None else np.asarray(points, dtype=float).copy()
    if p0.ndim != 2 or p0.shape[1] != 3 or len(p0) < 8:
        raise ValueError("points must have shape (N,3) with N>=8")
    n = int(len(p0))
    e0 = filament_energy(p0, force_python=force_python)
    sig0 = _shape_signature(p0)
    # Local dynamical scale ~ r_c/v_swirl; dt_factor keeps the short audit cheap/stable.
    dt = dt_factor * R_C / (GAMMA_CANON / (2.0 * math.pi * R_C))
    axis = np.array([0.0, 0.0, 1.0])
    dirs = {
        "x": np.array([1.0, 0.0, 0.0]),
        "y": np.array([0.0, 1.0, 0.0]),
        "z": np.array([0.0, 0.0, 1.0]),
        "diag": np.array([1.0, 1.0, 1.0]) / math.sqrt(3.0),
    }
    # Reference evolution at W=0 removes intrinsic discretization evolution.
    pref = evolve_filament(p0, dt=dt, steps=steps, background=(0,0,0), force_python=force_python)
    eref = filament_energy(pref, force_python=force_python)
    sigref = _shape_signature(pref)

    rows: list[dict[str, Any]] = []
    for beta in beta_values:
        for name, d in dirs.items():
            bg = beta * C * d
            p = evolve_filament(p0, dt=dt, steps=steps, background=bg, force_python=force_python)
            e = filament_energy(p, force_python=force_python)
            sig = _shape_signature(p)
            beta2 = float(beta * beta)
            mu2 = float(beta2 * (np.dot(d, axis) ** 2))
            # Optional synthetic term is ONLY a fit-recovery harness, not SST physics.
            injected = inject_chi0 * beta2 + inject_chi2 * (mu2 - beta2/3.0)
            dE = (e - eref) / eref + injected
            rows.append({
                "direction": name,
                "beta": float(beta),
                "beta2": beta2,
                "axis_projection_sq": mu2,
                "energy_J": float(e),
                "delta_E_over_E0": float(dE),
                "shape_rel_error": float(np.linalg.norm(sig-sigref) / max(np.linalg.norm(sigref), 1e-300)),
            })
    fit = fit_drift_sensitivity(rows)
    max_energy_dev = max(abs(r["delta_E_over_E0"] - (
        inject_chi0*r["beta2"] + inject_chi2*(r["axis_projection_sq"]-r["beta2"]/3.0)
    )) for r in rows)
    max_shape_dev = max(abs(r["shape_rel_error"]) for r in rows)
    tol = 5e-10 if force_python else 5e-9
    baseline_ok = max_energy_dev < tol and max_shape_dev < 1e-8
    return {
        "audit": "galilean_uniform_drift_baseline",
        "scope": "unmodified incompressible Euler filament baseline; not the full SST theory",
        "backend": backend_name(force_python=force_python),
        "n": n,
        "geometry_source": "torus_knot_T(2,3)_seed" if points is None else "external_points",
        "steps": steps,
        "dt_s": dt,
        "initial_energy_J": e0,
        "reference_energy_J": eref,
        "fit": fit,
        "injected_chi0": inject_chi0,
        "injected_chi2": inject_chi2,
        "max_baseline_energy_rel_deviation": max_energy_dev,
        "max_shape_rel_deviation": max_shape_dev,
        "baseline_ok": bool(baseline_ok),
        "interpretation": (
            "PASS_BASELINE_EULER: uniform drift does not create intrinsic preferred-frame sensitivity. "
            "Any SST nonzero chi must enter through additional constitutive/clock/background structure."
            if baseline_ok else
            "FAIL_BASELINE_NUMERICS: apparent preferred-frame response exceeds the numerical baseline tolerance."
        ),
        "rows": rows,
    }


def j1738_corrected_pdot(model_pdot_corr: float | None = None) -> dict[str, Any]:
    corr = J1738_PDOT_OBS - J1738_PDOT_SHK - J1738_PDOT_GAL
    sigma = math.sqrt(J1738_PDOT_OBS_SIGMA**2 + J1738_PDOT_SHK_SIGMA**2 + J1738_PDOT_GAL_SIGMA**2)
    out: dict[str, Any] = {
        "pdot_obs_s_per_s": J1738_PDOT_OBS,
        "pdot_shklovskii_s_per_s": J1738_PDOT_SHK,
        "pdot_galactic_s_per_s": J1738_PDOT_GAL,
        "pdot_corrected_s_per_s": corr,
        "pdot_corrected_sigma_s_per_s": sigma,
        "source": "Vaglio et al. 2026, arXiv:2605.01436",
        "status": "NOT_EVALUATED_NO_SST_PDOT_MODEL",
    }
    if model_pdot_corr is not None:
        z = (float(model_pdot_corr) - corr) / sigma
        out.update({
            "model_pdot_corr_s_per_s": float(model_pdot_corr),
            "z_score": float(z),
            "status": "PASS_2SIGMA" if abs(z) <= 2.0 else "FALSIFIED_AT_GT_2SIGMA_PROXY",
            "warning": "Gaussian proxy only; full timing posterior should replace this gate for publication-level inference.",
        })
    return out


def preferred_frame_gate(alpha1_eff: float | None = None, alpha2_eff: float | None = None) -> dict[str, Any]:
    c1_cap_90 = abs(J1738_ALPHA1_LOWER_90) / V_SWIRL_OVER_C_SQ
    c2_cap_ss = SOLAR_SYSTEM_ALPHA2_ABS / V_SWIRL_OVER_C_SQ
    out: dict[str, Any] = {
        "v_swirl_over_c_sq": V_SWIRL_OVER_C_SQ,
        "diagnostic_scaling": "alpha_eff = C * (v_swirl/c)^2",
        "C1_cap_from_J1738_90_one_sided_magnitude_proxy": c1_cap_90,
        "C2_cap_from_solar_system_abs_proxy": c2_cap_ss,
        "j1738_alpha1_lower_68": J1738_ALPHA1_LOWER_68,
        "j1738_alpha1_lower_90": J1738_ALPHA1_LOWER_90,
        "solar_system_alpha1_abs_quoted": SOLAR_SYSTEM_ALPHA1_ABS,
        "solar_system_alpha2_abs_quoted": SOLAR_SYSTEM_ALPHA2_ABS,
        "status": "NOT_EVALUATED_NO_SST_MAPPING",
        "warning": "No identity between SST coefficients and PPN alpha1/alpha2 is assumed. Supply an independently derived effective mapping.",
    }
    checks = {}
    if alpha1_eff is not None:
        # Paper prior/domain uses alpha1 <= 0, so apply the published one-sided lower bound only in that domain.
        a1 = float(alpha1_eff)
        checks["alpha1"] = {
            "value": a1,
            "domain_applicable": a1 <= 0.0,
            "pass_J1738_90_one_sided": bool(a1 >= J1738_ALPHA1_LOWER_90) if a1 <= 0 else None,
        }
    if alpha2_eff is not None:
        a2 = float(alpha2_eff)
        checks["alpha2"] = {
            "value": a2,
            "pass_solar_system_abs_proxy": bool(abs(a2) <= SOLAR_SYSTEM_ALPHA2_ABS),
        }
    if checks:
        passes = []
        for c in checks.values():
            for k,v in c.items():
                if k.startswith("pass_") and v is not None:
                    passes.append(bool(v))
        out["checks"] = checks
        out["status"] = "PASS_AVAILABLE_GATES" if passes and all(passes) else ("FAIL_AVAILABLE_GATES" if passes else "INCONCLUSIVE")
    return out


def dipole_universality_gate(objects: list[dict[str, float]], tolerance: float = 1e-10) -> dict[str, Any]:
    if len(objects) < 2:
        raise ValueError("Need at least two objects with mass and charge.")
    ratios = []
    for obj in objects:
        m = float(obj["mass"]); q = float(obj["charge"])
        if m == 0.0: raise ValueError("mass cannot be zero")
        ratios.append(q/m)
    ratios_np = np.asarray(ratios, dtype=float)
    mean = float(np.mean(ratios_np))
    scale = max(abs(mean), float(np.max(np.abs(ratios_np))), 1e-300)
    max_rel = float(np.max(np.abs(ratios_np-mean))/scale)
    pairs = []
    for i in range(len(objects)):
        for j in range(i+1, len(objects)):
            delta = ratios[i]-ratios[j]
            pairs.append({
                "a": objects[i].get("name", str(i)),
                "b": objects[j].get("name", str(j)),
                "delta_q_over_m": float(delta),
                "dipole_power_proxy_delta_sq": float(delta*delta),
            })
    ok = max_rel <= tolerance
    return {
        "audit": "universal_charge_to_mass_ratio",
        "ratios": ratios,
        "mean_ratio": mean,
        "max_relative_nonuniversality": max_rel,
        "tolerance": tolerance,
        "universal_within_tolerance": bool(ok),
        "pairs": pairs,
        "status": "PASS_NO_DIPOLE_FROM_Q_OVER_M_MISMATCH" if ok else "FAIL_UNIVERSALITY_DIPOLE_CHANNEL_OPEN",
        "warning": "The normalization of a physical SST radiation power is not assumed; delta^2 is only the universal dipole mismatch factor.",
    }


def linear_euler_bulk_wave_gate(k_vectors: list[list[float]] | None = None) -> dict[str, Any]:
    """Linearized homogeneous incompressible Euler about rest: projected du/dt=0, hence omega=0 modes."""
    if k_vectors is None:
        k_vectors = [[1,0,0], [1,1,0], [1,2,3]]
    rows = []
    max_abs_eig = 0.0
    for kv in k_vectors:
        k = np.asarray(kv, dtype=float)
        k2 = float(np.dot(k,k))
        if k2 == 0: continue
        P = np.eye(3) - np.outer(k,k)/k2
        # With no restoring term and after incompressibility projection: du_hat/dt = 0.
        A = np.zeros((3,3)) @ P
        eig = np.linalg.eigvals(A)
        max_abs_eig = max(max_abs_eig, float(np.max(np.abs(eig))))
        rows.append({"k": kv, "eigenvalues": [[float(z.real), float(z.imag)] for z in eig]})
    return {
        "audit": "linearized_homogeneous_incompressible_euler_bulk_wave",
        "max_abs_eigenvalue_per_s": max_abs_eig,
        "propagating_bulk_mode_found": False,
        "status": "STRUCTURAL_NO_BULK_WAVE_IN_THIS_BASELINE",
        "interpretation": "This falsifies only the claim that ordinary linear waves arise from homogeneous incompressible Euler about rest without additional structure; it does not exclude Kelvin waves or structured-background modes.",
        "rows": rows,
    }


def energy_balance_gate(t, e_orbit, flux_inf, p_rr, rel_tolerance: float = 0.05) -> dict[str, Any]:
    t = np.asarray(t, dtype=float)
    E = np.asarray(e_orbit, dtype=float)
    F = np.asarray(flux_inf, dtype=float)
    Prr = np.asarray(p_rr, dtype=float)
    if not (len(t)==len(E)==len(F)==len(Prr)) or len(t)<3:
        raise ValueError("t, e_orbit, flux_inf, p_rr must have equal length >=3")
    dEdt = np.gradient(E, t)
    # Desired closure: dE/dt = -F = P_rr, with F >= 0 as outward power.
    scale = np.maximum.reduce([np.abs(dEdt), np.abs(F), np.abs(Prr), np.full_like(dEdt, 1e-300)])
    res_flux = (dEdt + F)/scale
    res_rr = (dEdt - Prr)/scale
    rms_flux = float(np.sqrt(np.mean(res_flux**2)))
    rms_rr = float(np.sqrt(np.mean(res_rr**2)))
    ok = rms_flux <= rel_tolerance and rms_rr <= rel_tolerance
    return {
        "audit": "energy_balance_closure",
        "rms_relative_flux_residual": rms_flux,
        "rms_relative_radiation_reaction_residual": rms_rr,
        "relative_tolerance": rel_tolerance,
        "status": "PASS_CLOSURE" if ok else "FAIL_CLOSURE",
        "ok": bool(ok),
    }
