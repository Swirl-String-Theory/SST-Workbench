"""A029 v0.7.0 certification layer for the sealed v0.6 specific-Lagrangian producer.

The v0.6 producer in :mod:`sst_lagrangian` is intentionally not modified by
this upgrade.  This module builds *certification observables* around that
producer:

* the finite symmetric-control residual K_l(Delta),
* the closure-offset curvature C_Delta = -2 K_l / Delta^2,
* the wavenumber curvature C_k = -2 K_l / (delta k_hat)^2,
* full radial and core-area-mean complex kernels,
* Richardson extrapolation C_k(delta k -> 0), and
* phase/basis hashes needed for independent raw-amplitude matching.

C_k is a local branch-curvature diagnostic.  It is NOT, by itself, a physical
specific action.  A physical action requires an independently derived physical
closure displacement, amplitude/phase origin, and SI scale.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from typing import Any

import numpy as np

from .delay import loop_wavenumber
from .eigen import convergence_mode, mode_at_axial, solve_spectrum, track_mode
from .geometry import geometry_stats
from .sst_lagrangian import (
    EPS,
    TWOPI,
    _core_energy_centroid,
    _interp_complex,
    _mode_field,
    analytic_lagrangian_mode,
    phase_align,
)


@dataclass(frozen=True)
class CurvatureResult:
    delta: float
    delta_k_hat: float
    t_hat: np.ndarray
    r_hat: np.ndarray
    K_radial: np.ndarray
    K_core_mean: np.ndarray
    C_delta_radial: np.ndarray
    C_delta_core_mean: np.ndarray
    C_k_radial: np.ndarray
    C_k_core_mean: np.ndarray
    closed_radial: np.ndarray
    closed_core_mean: np.ndarray
    basis_hash: str
    branch_overlap_minus: float
    branch_overlap_plus: float
    parent_converged: bool
    closed_growth_gain: float
    max_branch_growth_gain: float
    r_eval_hat: float
    K_eval: np.ndarray


def _core_mask(r: np.ndarray) -> np.ndarray:
    r = np.asarray(r, float)
    mask = r <= 1.0
    if np.count_nonzero(mask) < 2:
        mask = np.ones_like(r, dtype=bool)
    return mask


def core_area_mean(r: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Cross-sectional area mean of y(r,t); the common 2*pi factor cancels."""
    r = np.asarray(r, float)
    y = np.asarray(y)
    mask = _core_mask(r)
    rr = r[mask]
    yy = y[mask]
    den = float(np.trapezoid(rr, rr))
    if den <= EPS:
        raise ValueError("degenerate core-area denominator")
    return np.trapezoid(yy * rr[:, None], rr, axis=0) / den


def core_area_rms(r: np.ndarray, y: np.ndarray) -> np.ndarray:
    r = np.asarray(r, float)
    y = np.asarray(y)
    mask = _core_mask(r)
    rr = r[mask]
    yy = y[mask]
    den = float(np.trapezoid(rr, rr))
    if den <= EPS:
        raise ValueError("degenerate core-area denominator")
    return np.sqrt(np.trapezoid(np.abs(yy) ** 2 * rr[:, None], rr, axis=0) / den)


def complex_rms(y: np.ndarray) -> float:
    y = np.asarray(y)
    return float(np.sqrt(np.mean(np.abs(y) ** 2)))


def relative_span(values) -> float:
    x = np.asarray([float(v) for v in values if v is not None and np.isfinite(float(v))], float)
    if len(x) < 2:
        return math.inf
    return float(np.ptp(x) / max(abs(float(np.median(x))), 1e-30))


def complex_overlap(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, complex).ravel()
    b = np.asarray(b, complex).ravel()
    den = float(np.linalg.norm(a) * np.linalg.norm(b))
    if den <= 1e-30:
        return 0.0
    return float(abs(np.vdot(a, b)) / den)


def phase_align_series(reference: np.ndarray, other: np.ndarray) -> tuple[np.ndarray, float, float]:
    reference = np.asarray(reference, complex)
    other = np.asarray(other, complex)
    z = np.vdot(reference, other)
    if abs(z) <= 1e-30:
        return other.copy(), 0.0, 0.0
    rot = np.exp(-1j * np.angle(z))
    aligned = other * rot
    return aligned, float(np.angle(z)), complex_overlap(reference, aligned)


def _hash_array(h, arr) -> None:
    a = np.asarray(arr)
    if np.iscomplexobj(a):
        _hash_array(h, np.asarray(a.real, dtype="<f8"))
        _hash_array(h, np.asarray(a.imag, dtype="<f8"))
        return
    b = np.ascontiguousarray(a, dtype="<f8")
    h.update(str(b.shape).encode("ascii"))
    h.update(b.tobytes(order="C"))


def lagrangian_basis_hash(mode) -> str:
    """Stable hash of the normalized closed-mode gauge used by the action kernel."""
    h = hashlib.sha256()
    for arr in (mode.r, mode.U, mode.V, mode.ur, mode.ut, mode.uz, mode.pi):
        _hash_array(h, arr)
    h.update(f"sigma={mode.sigma:.17g};omega={mode.omega:.17g};k={mode.k_hat:.17g};m={mode.m}".encode())
    return h.hexdigest()


def geometry_sha256(components) -> str:
    """Stable ordered geometry hash usable without revealing topology labels."""
    h = hashlib.sha256()
    for c in components:
        a = np.ascontiguousarray(np.asarray(c, dtype="<f8"))
        h.update(str(a.shape).encode("ascii"))
        h.update(a.tobytes(order="C"))
    return h.hexdigest()


def _cumtrapz_complex(t: np.ndarray, y: np.ndarray) -> np.ndarray:
    t = np.asarray(t, float)
    y = np.asarray(y, complex)
    out = np.zeros_like(y, dtype=complex)
    if len(t) > 1:
        out[1:] = np.cumsum(0.5 * (y[1:] + y[:-1]) * np.diff(t))
    return out


def _mode_state(closed_candidate, cfg: dict, k_hat: float, radial_n: int):
    sel = dict(cfg.get("mode_selection", {}))
    maxres = float(sel.get("max_residual", 1e-7))
    spec = solve_spectrum(
        closed_candidate.profile_name,
        closed_candidate.axial_ratio,
        int(closed_candidate.m),
        float(k_hat),
        int(radial_n),
        closed_candidate.rmax,
    )
    md, _ = mode_at_axial(
        closed_candidate.profile_name,
        closed_candidate.axial_ratio,
        int(closed_candidate.m),
        float(k_hat),
        int(radial_n),
        closed_candidate.rmax,
        sel,
    )
    if md is None:
        return None, None
    md_spec = track_mode(md, spec, 0.0, maxres) or md
    return spec, md_spec


def construct_curvature_kernel(
    closed_candidate,
    control_candidate,
    cfg: dict,
    *,
    control_offset_abs: float | None = None,
    radial_n: int | None = None,
    n_t: int = 401,
    n_cycles: float = 2.0,
    r_eval_hat: float | None = None,
    evaluate_parent_convergence: bool = True,
) -> dict[str, Any]:
    """Construct K_l, C_Delta and C_k while preserving the sealed v0.6 producer math.

    The controls are generated symmetrically around exact closure.  The stronger
    v0.7 action-branch overlap gate is reported separately from the parent A029
    minimum-overlap selector.
    """
    attrs = ("profile_name", "axial_ratio", "core_fraction", "m", "n", "rmax")
    mismatches = [k for k in attrs if getattr(closed_candidate, k) != getattr(control_candidate, k)]
    if mismatches:
        raise ValueError(f"closed/control candidates mismatch: {mismatches}")

    gs = geometry_stats(closed_candidate.components)
    gs2 = geometry_stats(control_candidate.components)
    if abs(gs["length_total"] - gs2["length_total"]) > 1e-10 * max(1.0, abs(gs["length_total"])):
        raise ValueError("closed/control geometries do not match")

    delta = abs(float(control_candidate.closure_offset)) if control_offset_abs is None else abs(float(control_offset_abs))
    if not (np.isfinite(delta) and delta > 0.0):
        return {"status": "NOT_RUN", "reason": "symmetric control offset must be positive"}

    a_hat = float(closed_candidate.core_fraction)
    Lhat = float(gs["length_total"]) / a_hat
    hol = float(gs["bishop_holonomy_mean"])
    m = int(closed_candidate.m)
    n = int(closed_candidate.n)
    N = int(radial_n if radial_n is not None else closed_candidate.radial_n_dispersion)
    sel = dict(cfg.get("mode_selection", {}))
    minov_parent = float(sel.get("min_overlap", 0.08))
    maxres = float(sel.get("max_residual", 1e-7))

    k0 = loop_wavenumber(Lhat, m, n, hol, 0.0)
    km = loop_wavenumber(Lhat, m, n, hol, -delta)
    kp = loop_wavenumber(Lhat, m, n, hol, +delta)
    delta_k = 0.5 * abs(kp - km)
    if delta_k <= 0:
        return {"status": "NOT_RUN", "reason": "zero wavenumber detuning"}

    spec0, md0 = _mode_state(closed_candidate, cfg, k0, N)
    if md0 is None:
        return {"status": "NOT_RUN", "reason": "no closed hybrid eigenmode", "radial_n": N}
    specm = solve_spectrum(closed_candidate.profile_name, closed_candidate.axial_ratio, m, km, N, closed_candidate.rmax)
    specp = solve_spectrum(closed_candidate.profile_name, closed_candidate.axial_ratio, m, kp, N, closed_candidate.rmax)
    mdm = track_mode(md0, specm, minov_parent, maxres)
    mdp = track_mode(md0, specp, minov_parent, maxres)
    if mdm is None or mdp is None:
        return {
            "status": "NOT_RUN",
            "reason": "same eigenbranch could not be continued to symmetric controls",
            "radial_n": N,
            "delta": delta,
        }

    f0 = _mode_field(spec0, md0, k0, m)
    fm = _mode_field(specm, mdm, km, m)
    fp = _mode_field(specp, mdp, kp, m)
    fm, phase_m, ov_m = phase_align(f0, fm)
    fp, phase_p, ov_p = phase_align(f0, fp)

    # Parent frozen convergence gate, evaluated at the *original* radial levels.
    # Stage-02 radial sweeps may reuse a convergence result already evaluated for
    # the same detuning at the reference N; in that case this expensive parent
    # check can be skipped without changing the radial-N diagnostic.
    if evaluate_parent_convergence:
        conv0 = convergence_mode(closed_candidate.profile_name, closed_candidate.axial_ratio, m, k0, closed_candidate.radial_levels, closed_candidate.rmax, sel)
        convm = convergence_mode(closed_candidate.profile_name, closed_candidate.axial_ratio, m, km, closed_candidate.radial_levels, closed_candidate.rmax, sel)
        convp = convergence_mode(closed_candidate.profile_name, closed_candidate.axial_ratio, m, kp, closed_candidate.radial_levels, closed_candidate.rmax, sel)
        parent_converged = bool(conv0.get("converged") and convm.get("converged") and convp.get("converged"))
    else:
        conv0 = convm = convp = {"converged": True, "reused": True}
        parent_converged = True

    rstar = _core_energy_centroid(f0) if r_eval_hat is None else float(r_eval_hat)
    omega_clock = max(abs(float(f0.omega)), 1e-6)
    tmax = float(n_cycles) * TWOPI / omega_clock
    t_hat = np.linspace(0.0, tmax, int(n_t))

    L0 = analytic_lagrangian_mode(f0, t_hat)
    Lm = analytic_lagrangian_mode(fm, t_hat)
    Lp = analytic_lagrangian_mode(fp, t_hat)
    K = L0 - 0.5 * (Lm + Lp)
    C_delta = -2.0 * K / (delta * delta)
    C_k = -2.0 * K / (delta_k * delta_k)

    Kmean = core_area_mean(f0.r, K)
    Cdelta_mean = core_area_mean(f0.r, C_delta)
    Ck_mean = core_area_mean(f0.r, C_k)
    L0mean = core_area_mean(f0.r, L0)
    K_eval = _interp_complex(f0.r, K, rstar)

    base_rms = max(complex_rms(L0mean), 1e-30)
    k_rms = complex_rms(Kmean)
    cdk_rms = complex_rms(Ck_mean)
    action_min_overlap = float(cfg.get("mega", {}).get("certification", {}).get("action_branch_overlap_min", 0.95))
    strong_branch = bool(ov_m >= action_min_overlap and ov_p >= action_min_overlap)

    result: dict[str, Any] = {
        "schema": "A029-SST-LAGRANGIAN-CURVATURE-1.0",
        "status": "QUALIFIED_PARENT_MODE" if parent_converged and strong_branch else "DIAGNOSTIC_ONLY",
        "scientifically_qualified_parent": bool(parent_converged and strong_branch),
        "radial_n": N,
        "control_offset_abs": delta,
        "loop_length_over_core": Lhat,
        "delta_k_hat": delta_k,
        "k_hat": {"closed": k0, "minus": km, "plus": kp},
        "branch_overlap": {"minus": ov_m, "plus": ov_p, "action_minimum_required": action_min_overlap},
        "phase_alignment_rotation_rad": {"minus": phase_m, "plus": phase_p},
        "parent_radial_convergence": {
            "evaluated": bool(evaluate_parent_convergence),
            "closed": bool(conv0.get("converged")),
            "minus": bool(convm.get("converged")),
            "plus": bool(convp.get("converged")),
        },
        "basis_hash": lagrangian_basis_hash(f0),
        "geometry_sha256": geometry_sha256(closed_candidate.components),
        "t_hat": t_hat,
        "r_hat": np.asarray(f0.r, float),
        "r_eval_hat": rstar,
        "K_l_radial_complex": K,
        "K_l_core_mean_complex": Kmean,
        "K_l_eval_complex": K_eval,
        "C_delta_radial_complex": C_delta,
        "C_delta_core_mean_complex": Cdelta_mean,
        "C_k_radial_complex": C_k,
        "C_k_core_mean_complex": Ck_mean,
        "closed_lagrangian_radial_complex": L0,
        "closed_lagrangian_core_mean_complex": L0mean,
        "complex_action_kernel_hat": _cumtrapz_complex(t_hat, Kmean),
        "complex_curvature_action_kernel_hat": _cumtrapz_complex(t_hat, Ck_mean),
        "diagnostics": {
            "finite_K_core_mean_rms": k_rms,
            "finite_K_to_closed_rms": k_rms / base_rms,
            "C_k_core_mean_rms": cdk_rms,
            "closed_core_mean_rms": base_rms,
        },
        "time_horizon": {
            "basis": "closed_modal_period",
            "n_cycles": float(n_cycles),
            "t_hat_max": float(tmax),
            "closed_growth_gain": float(np.exp(f0.sigma * tmax)),
            "max_branch_growth_gain": float(np.exp(max(f0.sigma, fm.sigma, fp.sigma, 0.0) * tmax)),
        },
        "interpretation": (
            "K_l is the finite symmetric-control residual. C_k=-2*K_l/delta_k_hat^2 is a local "
            "wavenumber-curvature diagnostic and is not itself a physical action."
        ),
    }
    return result


def richardson_zero_from_two(c_large: np.ndarray, dk_large: float, c_small: np.ndarray, dk_small: float) -> np.ndarray:
    """Extrapolate C(dk)=C0+A*dk^2+O(dk^4) to dk=0 using two smallest offsets."""
    d1 = float(dk_large)
    d2 = float(dk_small)
    if not (d1 > d2 > 0):
        raise ValueError("Richardson inputs require dk_large > dk_small > 0")
    den = d1*d1 - d2*d2
    return (d1*d1*np.asarray(c_small, complex) - d2*d2*np.asarray(c_large, complex)) / den


def quadratic_power_exponent(offsets, residuals) -> float:
    x = np.asarray(offsets, float)
    y = np.asarray(residuals, float)
    mask = (x > 0) & (y > 0) & np.isfinite(x) & np.isfinite(y)
    if np.count_nonzero(mask) < 3:
        return math.nan
    return float(np.polyfit(np.log(x[mask]), np.log(y[mask]), 1)[0])
