from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy.interpolate import CubicSpline

from .contact import PeriodicLiftMap
from .geometry import PeriodicCurve


@dataclass
class ForceBalanceResult:
    s: np.ndarray
    force_in: np.ndarray
    force_out: np.ndarray
    scalar_in: np.ndarray
    scalar_out: np.ndarray
    local_balance_residual: np.ndarray
    compatibility_residual: np.ndarray
    inverse_compatibility_residual: np.ndarray
    compatibility_relative_l2: float
    inverse_compatibility_relative_l2: float
    local_balance_relative_l2: float
    determinant_abs: np.ndarray
    ill_conditioned_fraction: float
    sigma_derivative: np.ndarray
    tau_derivative: np.ndarray


def _periodic_scalar_spline(s: np.ndarray, values: np.ndarray):
    valid = np.isfinite(values)
    if np.sum(valid) < 4:
        return lambda q: np.full_like(np.asarray(q, dtype=float), np.nan, dtype=float)
    # Fill rare ill-conditioned samples periodically before constructing the spline.
    idx = np.arange(len(values), dtype=float)
    idx_valid = idx[valid]
    val_valid = values[valid]
    idx_ext = np.r_[idx_valid[-1] - len(values), idx_valid, idx_valid[0] + len(values)]
    val_ext = np.r_[val_valid[-1], val_valid, val_valid[0]]
    filled = np.interp(idx, idx_ext, val_ext)
    spline = CubicSpline(np.r_[s, 1.0], np.r_[filled, filled[0]], bc_type="periodic")
    return lambda q: spline(np.mod(q, 1.0))


def geometric_force_balance(
    curve: PeriodicCurve,
    s: np.ndarray,
    sigma: PeriodicLiftMap,
    tau: PeriodicLiftMap,
    determinant_floor: float = 1e-6,
) -> ForceBalanceResult:
    """Evaluate Carlen's two-contact force decomposition and scalar compatibility.

    The local system resolves the two chord-directed force densities so that

        F^I u_I + F^O u_O + kappa n = 0.

    The nonlocal compatibility tests the thesis relation

        F^O(s) = -F^I(sigma(s)) sigma'(s),

    and its tau counterpart.  No force scale is fitted in this stage.
    """
    s = np.asarray(s, dtype=float)
    p = curve.eval(s)
    _, kv, kappa, n, b = curve.frame(s)
    sig = sigma.mod(s)
    ta = tau.mod(s)
    p_sig = curve.eval(sig)
    p_tau = curve.eval(ta)
    c_out = p - p_sig
    c_in = p - p_tau
    u_out = c_out / np.maximum(np.linalg.norm(c_out, axis=1, keepdims=True), 1e-15)
    u_in = c_in / np.maximum(np.linalg.norm(c_in, axis=1, keepdims=True), 1e-15)

    ncomp_in = np.sum(u_in * n, axis=1)
    bcomp_in = np.sum(u_in * b, axis=1)
    ncomp_out = np.sum(u_out * n, axis=1)
    bcomp_out = np.sum(u_out * b, axis=1)
    det = ncomp_in * bcomp_out - ncomp_out * bcomp_in

    f_in = np.full(len(s), np.nan)
    f_out = np.full(len(s), np.nan)
    good = np.abs(det) > determinant_floor
    # Solve [nI nO; bI bO] [FI,FO]^T = [-kappa, 0]^T.
    f_in[good] = -kappa[good] * bcomp_out[good] / det[good]
    f_out[good] = kappa[good] * bcomp_in[good] / det[good]
    force_in = f_in[:, None] * u_in
    force_out = f_out[:, None] * u_out
    total = force_in + force_out + kv
    local_norm = np.linalg.norm(total, axis=1)
    local_den = np.maximum(kappa, 1e-15)

    eval_f_in = _periodic_scalar_spline(s, f_in)
    eval_f_out = _periodic_scalar_spline(s, f_out)
    sig_prime = sigma.derivative(s)
    tau_prime = tau.derivative(s)

    compatibility_signed = f_out + eval_f_in(sig) * sig_prime
    inverse_signed = f_in + eval_f_out(ta) * tau_prime
    compatibility = np.abs(compatibility_signed)
    inverse_compatibility = np.abs(inverse_signed)

    scale = np.abs(f_out) + np.abs(eval_f_in(sig) * sig_prime)
    inverse_scale = np.abs(f_in) + np.abs(eval_f_out(ta) * tau_prime)
    valid = good & np.isfinite(compatibility) & (scale > 1e-15)
    valid_inverse = good & np.isfinite(inverse_compatibility) & (inverse_scale > 1e-15)
    comp_rel = (
        float(np.sqrt(np.mean(compatibility[valid] ** 2)) / np.sqrt(np.mean(scale[valid] ** 2)))
        if np.any(valid) else float("inf")
    )
    inv_comp_rel = (
        float(np.sqrt(np.mean(inverse_compatibility[valid_inverse] ** 2)) / np.sqrt(np.mean(inverse_scale[valid_inverse] ** 2)))
        if np.any(valid_inverse) else float("inf")
    )
    local_rel = float(np.sqrt(np.nanmean((local_norm / local_den) ** 2)))
    return ForceBalanceResult(
        s=s,
        force_in=force_in,
        force_out=force_out,
        scalar_in=f_in,
        scalar_out=f_out,
        local_balance_residual=local_norm,
        compatibility_residual=compatibility,
        inverse_compatibility_residual=inverse_compatibility,
        compatibility_relative_l2=comp_rel,
        inverse_compatibility_relative_l2=inv_comp_rel,
        local_balance_relative_l2=local_rel,
        determinant_abs=np.abs(det),
        ill_conditioned_fraction=float(np.mean(~good)),
        sigma_derivative=sig_prime,
        tau_derivative=tau_prime,
    )
