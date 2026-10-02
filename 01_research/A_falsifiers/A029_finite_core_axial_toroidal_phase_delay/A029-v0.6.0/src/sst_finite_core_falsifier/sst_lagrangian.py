"""A029 closure-residual specific-Lagrangian kernel.

Constructs the *linear-order* material-parcel specific-Lagrangian perturbation
carried by an A029 Euler eigenmode, and subtracts the preregistered symmetric
+/- closure-detuning control.

The result is deliberately split into:
  1. a dimensionless, phase-covariant A029 kernel K_l(r,t_hat), and
  2. an optional SI realization after independent length/velocity/amplitude
     scales are supplied.

No legacy loop phase is re-labelled as an action.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .delay import loop_wavenumber
from .eigen import mode_at_axial, solve_spectrum, track_mode, vector_overlap, convergence_mode
from .geometry import geometry_stats

TWOPI = 2.0 * np.pi
EPS = 1e-30


@dataclass(frozen=True)
class ModeField:
    r: np.ndarray
    U: np.ndarray
    V: np.ndarray
    ur: np.ndarray
    ut: np.ndarray
    uz: np.ndarray
    pi: np.ndarray  # specific-pressure perturbation, scaled by V0^2
    sigma: float
    omega: float
    k_hat: float
    m: int
    normalization: str = "core_rms_velocity_unity"


def _core_rms_velocity_norm(r: np.ndarray, ur, ut, uz) -> float:
    r = np.asarray(r, float)
    e = np.abs(ur) ** 2 + np.abs(ut) ** 2 + np.abs(uz) ** 2
    mask = r <= 1.0
    if np.count_nonzero(mask) < 2:
        mask = np.ones_like(r, dtype=bool)
    rr = r[mask]
    ee = e[mask]
    den = float(np.trapezoid(rr, rr))  # integral r dr
    num = float(np.trapezoid(ee * rr, rr))
    if not np.isfinite(num) or num <= EPS or den <= EPS:
        raise ValueError("mode has zero/non-finite core velocity norm")
    return float(np.sqrt(num / den))


def _mode_field(spec: dict, mode: dict, k_hat: float, m: int) -> ModeField:
    r = np.asarray(spec["r"], float)
    U = np.asarray(spec["U"], float)
    V = np.asarray(spec["V"], float)
    q = np.asarray(mode["vector"], complex).copy()
    N = len(r)
    ur, ut, uz, pi = q[:N], q[N:2*N], q[2*N:3*N], q[3*N:4*N]
    norm = _core_rms_velocity_norm(r, ur, ut, uz)
    ur, ut, uz, pi = ur/norm, ut/norm, uz/norm, pi/norm
    lam = complex(mode["lambda"])
    return ModeField(r, U, V, ur, ut, uz, pi, float(lam.real), float(-lam.imag), float(k_hat), int(m))


def _weighted_velocity_overlap(a: ModeField, b: ModeField) -> complex:
    if len(a.r) != len(b.r) or np.max(np.abs(a.r - b.r)) > 1e-12:
        raise ValueError("mode radial grids must match for phase alignment")
    density = np.conj(a.ur)*b.ur + np.conj(a.ut)*b.ut + np.conj(a.uz)*b.uz
    return complex(np.trapezoid(density * a.r, a.r))


def phase_align(reference: ModeField, other: ModeField) -> tuple[ModeField, float, float]:
    """Fix the arbitrary complex eigenvector phase by positive overlap with reference."""
    z = _weighted_velocity_overlap(reference, other)
    if abs(z) <= EPS:
        raise ValueError("closed/control mode overlap is zero; phase cannot be aligned")
    rot = np.exp(-1j * np.angle(z))
    aligned = ModeField(
        other.r, other.U, other.V,
        other.ur*rot, other.ut*rot, other.uz*rot, other.pi*rot,
        other.sigma, other.omega, other.k_hat, other.m, other.normalization,
    )
    denom = np.sqrt(abs(_weighted_velocity_overlap(reference, reference))*abs(_weighted_velocity_overlap(aligned, aligned)))
    ov = abs(_weighted_velocity_overlap(reference, aligned))/max(float(denom), EPS)
    return aligned, float(np.angle(z)), float(ov)


def material_specific_lagrangian_coefficient(mode: ModeField) -> np.ndarray:
    """Complex coefficient C_l = U*u_z + V*u_theta - pi.

    For v=v0+epsilon*u' and p=p0+epsilon*p', the first-order parcel diagnostic

        delta l^(1) / V0^2 = epsilon Re[C_l exp(Psi)].

    The quadratic kinetic term is intentionally omitted: A029 is a linearized
    Euler model and does not supply the matching second-order pressure/state.
    """
    return mode.U*mode.uz + mode.V*mode.ut - mode.pi


def relative_frequency(mode: ModeField) -> np.ndarray:
    """omega_rel(r)=omega-[m V/r + k U] along a base-flow material trajectory."""
    re = np.asarray(mode.r, float).copy()
    if len(re) > 1:
        re[0] = max(0.5*re[1], 1e-10)
    else:
        re[0] = 1e-10
    adv = mode.m*mode.V/re + mode.k_hat*mode.U
    return mode.omega - adv


def analytic_lagrangian_mode(mode: ModeField, t_hat) -> np.ndarray:
    """Return complex phase-covariant first-order l-kernel, shape (n_r,n_t)."""
    t = np.asarray(t_hat, float)
    C = material_specific_lagrangian_coefficient(mode)
    wrel = relative_frequency(mode)
    return C[:, None] * np.exp(mode.sigma*t[None, :] - 1j*wrel[:, None]*t[None, :])


def _core_energy_centroid(mode: ModeField) -> float:
    e = np.abs(mode.ur)**2 + np.abs(mode.ut)**2 + np.abs(mode.uz)**2
    mask = mode.r <= 1.0
    if np.count_nonzero(mask) < 2:
        mask = np.ones_like(mode.r, dtype=bool)
    r = mode.r[mask]
    w = e[mask]*r
    den = float(np.trapezoid(w, r))
    if den <= EPS:
        raise ValueError("cannot determine core energy centroid")
    return float(np.trapezoid(r*w, r)/den)


def _interp_complex(r: np.ndarray, y: np.ndarray, x: float) -> np.ndarray:
    # y is (n_r,n_t)
    return np.array([np.interp(x, r, y[:,j].real) + 1j*np.interp(x, r, y[:,j].imag) for j in range(y.shape[1])])


def _cumtrapz(t: np.ndarray, y: np.ndarray) -> np.ndarray:
    out = np.zeros_like(y, dtype=float)
    if len(t) > 1:
        out[1:] = np.cumsum(0.5*(y[1:]+y[:-1])*np.diff(t))
    return out


def construct_closure_residual_kernel(
    closed_candidate,
    control_candidate,
    cfg: dict,
    *,
    n_t: int = 1201,
    n_cycles: float = 4.0,
    phase0_rad: float = 0.0,
    r_eval_hat: float | None = None,
    amplitude_epsilon: float | None = None,
    core_radius_m: float | None = None,
    velocity_scale_m_s: float | None = None,
) -> dict[str, Any]:
    """Construct delta-l_SST from the A029 CLOSED minus symmetric +/- control.

    The primary output is the dimensionless complex kernel K_l(t_hat).  A real
    physical signal is epsilon*V0^2*Re[e^{i phase0} K_l].  If epsilon is not
    independently supplied, the SI result is explicitly labelled per-unit-amplitude.
    """
    # The pair must differ only by closure condition.
    attrs = ("profile_name","axial_ratio","core_fraction","m","n","radial_n_dispersion","rmax")
    mismatches = [k for k in attrs if getattr(closed_candidate,k) != getattr(control_candidate,k)]
    if mismatches:
        raise ValueError(f"closed/control candidates mismatch: {mismatches}")

    gs = geometry_stats(closed_candidate.components)
    gs2 = geometry_stats(control_candidate.components)
    if abs(gs["length_total"]-gs2["length_total"]) > 1e-10*max(1.0,abs(gs["length_total"])):
        raise ValueError("closed/control geometries do not match")

    a_hat = float(closed_candidate.core_fraction)
    Lhat = float(gs["length_total"])/a_hat
    hol = float(gs["bishop_holonomy_mean"])
    m = int(closed_candidate.m); n = int(closed_candidate.n)
    d = abs(float(control_candidate.closure_offset))
    if d <= 0:
        d = abs(float(closed_candidate.closure_offset))
    if d < 0:
        raise ValueError("invalid closure offset")

    k0 = loop_wavenumber(Lhat,m,n,hol,0.0)
    km = loop_wavenumber(Lhat,m,n,hol,-d)
    kp = loop_wavenumber(Lhat,m,n,hol,+d)
    sel = dict(cfg.get("mode_selection",{}))
    N = int(closed_candidate.radial_n_dispersion)
    maxres = float(sel.get("max_residual",1e-7))
    minov = float(sel.get("min_overlap",.08))

    spec0 = solve_spectrum(closed_candidate.profile_name,closed_candidate.axial_ratio,m,k0,N,closed_candidate.rmax)
    md0, cont0 = mode_at_axial(closed_candidate.profile_name,closed_candidate.axial_ratio,m,k0,N,closed_candidate.rmax,sel)
    if md0 is None:
        return {"status":"NOT_RUN","reason":"no closed hybrid eigenmode","k0":k0}

    # Re-identify the selected closed mode in spec0 by overlap, then continue it in k.
    md0s = track_mode(md0,spec0,0.0,maxres) or md0
    specm = solve_spectrum(closed_candidate.profile_name,closed_candidate.axial_ratio,m,km,N,closed_candidate.rmax)
    specp = solve_spectrum(closed_candidate.profile_name,closed_candidate.axial_ratio,m,kp,N,closed_candidate.rmax)
    mdm = track_mode(md0s,specm,minov,maxres)
    mdp = track_mode(md0s,specp,minov,maxres)
    if mdm is None or mdp is None:
        return {"status":"NOT_RUN","reason":"same eigenbranch could not be continued to symmetric control","k0":k0,"km":km,"kp":kp}

    f0 = _mode_field(spec0,md0s,k0,m)
    fm = _mode_field(specm,mdm,km,m)
    fp = _mode_field(specp,mdp,kp,m)
    fm, phase_m, ov_m = phase_align(f0,fm)
    fp, phase_p, ov_p = phase_align(f0,fp)

    # Scientific qualification reuses the frozen radial convergence gate.
    conv0 = convergence_mode(closed_candidate.profile_name,closed_candidate.axial_ratio,m,k0,closed_candidate.radial_levels,closed_candidate.rmax,sel)
    convm = convergence_mode(closed_candidate.profile_name,closed_candidate.axial_ratio,m,km,closed_candidate.radial_levels,closed_candidate.rmax,sel)
    convp = convergence_mode(closed_candidate.profile_name,closed_candidate.axial_ratio,m,kp,closed_candidate.radial_levels,closed_candidate.rmax,sel)
    qualified = bool(conv0.get("converged") and convm.get("converged") and convp.get("converged") and ov_m>=minov and ov_p>=minov)

    # Frozen time grid.  Do NOT set the horizon from a near-zero material
    # relative frequency: FAST_SWIRL_LOCKED modes can make omega_rel tiny,
    # which would extrapolate an unstable linear eigenmode for many e-folds.
    # The parent A029 clock is the modal eigenfrequency, so use a fixed number
    # of CLOSED carrier periods and report the resulting linear gain.
    rstar = _core_energy_centroid(f0) if r_eval_hat is None else float(r_eval_hat)
    if not (f0.r[0] <= rstar <= f0.r[-1]):
        raise ValueError("r_eval_hat lies outside radial domain")
    omega_clock = max(abs(f0.omega),1e-6)
    tmax = float(n_cycles)*TWOPI/omega_clock
    t_hat = np.linspace(0.0,tmax,int(n_t))

    L0 = analytic_lagrangian_mode(f0,t_hat)
    Lm = analytic_lagrangian_mode(fm,t_hat)
    Lp = analytic_lagrangian_mode(fp,t_hat)
    K = L0 - 0.5*(Lm+Lp)
    Kstar = _interp_complex(f0.r,K,rstar)
    real_unit = np.real(np.exp(1j*float(phase0_rad))*Kstar)

    # Null/structure diagnostics.
    base_scale = max(float(np.sqrt(np.mean(np.abs(_interp_complex(f0.r,L0,rstar))**2))),EPS)
    residual_rms = float(np.sqrt(np.mean(real_unit**2)))
    residual_complex_rms = float(np.sqrt(np.mean(np.abs(Kstar)**2)))

    out: dict[str, Any] = {
        "schema":"A029-SST-SPECIFIC-LAGRANGIAN-KERNEL-1.0",
        "status":"QUALIFIED_DIMENSIONLESS_KERNEL" if qualified else "DIAGNOSTIC_DIMENSIONLESS_KERNEL",
        "scientifically_qualified":qualified,
        "definition":"CLOSED - 0.5*(CONTROL_- + CONTROL_+), linearized Euler parcel specific-Lagrangian kernel",
        "linear_order_only":True,
        "second_order_kinetic_term_included":False,
        "reason_second_order_omitted":"A029 supplies only a linearized Euler state; a consistent O(epsilon^2) pressure/state correction is unavailable.",
        "normalization":"each eigenmode has unit core-RMS perturbation velocity; epsilon is the independently measured core-RMS perturbation amplitude divided by V0",
        "phase_origin_semantics":"phase0 is not an A029 prediction; retain complex kernel until downstream geometry/interaction map fixes the physical phase origin",
        "t_hat":t_hat,
        "r_eval_hat":rstar,
        "K_l_complex":Kstar,
        "delta_l_hat_per_epsilon":real_unit,
        "k_hat":{"closed":k0,"control_minus":km,"control_plus":kp},
        "mode":{"closed":{"sigma":f0.sigma,"omega":f0.omega},"minus":{"sigma":fm.sigma,"omega":fm.omega},"plus":{"sigma":fp.sigma,"omega":fp.omega}},
        "branch_overlap":{"minus":ov_m,"plus":ov_p,"minimum_required":minov},
        "phase_alignment_rotation_rad":{"minus":phase_m,"plus":phase_p},
        "radial_convergence":{"closed":bool(conv0.get("converged")),"minus":bool(convm.get("converged")),"plus":bool(convp.get("converged")),"closed_omega_rel_span":conv0.get("omega_rel_span"),"minus_omega_rel_span":convm.get("omega_rel_span"),"plus_omega_rel_span":convp.get("omega_rel_span")},
        "dimensionless_diagnostics":{"residual_real_rms_per_epsilon":residual_rms,"residual_complex_rms_per_epsilon":residual_complex_rms,"residual_to_closed_rms":residual_complex_rms/base_scale},
        "time_horizon":{"basis":"closed_modal_period","n_cycles":float(n_cycles),"t_hat_max":float(tmax),"closed_growth_gain":float(np.exp(f0.sigma*tmax)),"max_branch_growth_gain":float(np.exp(max(f0.sigma,fm.sigma,fp.sigma,0.0)*tmax))},
        "absolute_amplitude_status":"INDEPENDENTLY_SUPPLIED" if amplitude_epsilon is not None else "NOT_SUPPLIED__PER_UNIT_EPSILON_ONLY",
    }

    if core_radius_m is not None and velocity_scale_m_s is not None:
        a_m = float(core_radius_m); V0 = float(velocity_scale_m_s)
        if not (np.isfinite(a_m) and a_m>0 and np.isfinite(V0) and V0>0):
            raise ValueError("core_radius_m and velocity_scale_m_s must be positive finite")
        eps = 1.0 if amplitude_epsilon is None else float(amplitude_epsilon)
        t_s = t_hat*a_m/V0
        dl_per_eps = V0*V0*real_unit
        ds_per_eps = a_m*V0*_cumtrapz(t_hat,real_unit)
        out["si"] = {
            "core_radius_m":a_m,
            "velocity_scale_m_s":V0,
            "time_unit_s":a_m/V0,
            "specific_lagrangian_unit_m2_s2":V0*V0,
            "specific_action_unit_m2_s":a_m*V0,
            "t_s":t_s,
            "delta_l_sst_per_epsilon_m2_s2":dl_per_eps,
            "delta_s_sst_per_epsilon_m2_s":ds_per_eps,
            "epsilon":None if amplitude_epsilon is None else eps,
            "delta_l_sst_m2_s2":None if amplitude_epsilon is None else eps*dl_per_eps,
            "delta_s_sst_m2_s":None if amplitude_epsilon is None else eps*ds_per_eps,
        }
    return out
