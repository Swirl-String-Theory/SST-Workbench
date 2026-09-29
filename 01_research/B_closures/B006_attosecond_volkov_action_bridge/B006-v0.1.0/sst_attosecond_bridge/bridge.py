from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class BridgeResult:
    amplitude_orthodox: np.ndarray
    amplitude_exact: np.ndarray
    amplitude_linear: np.ndarray
    intensity_orthodox: np.ndarray
    intensity_exact: np.ndarray
    delta_intensity_exact: np.ndarray
    delta_intensity_linear: np.ndarray
    phase: np.ndarray


def phase_from_action(delta_action_J_s, reduced_action_quantum_J_s):
    """Return δφ = δS/ħ. Both inputs must have units J s."""
    denom = float(reduced_action_quantum_J_s)
    if not np.isfinite(denom) or denom <= 0.0:
        raise ValueError("reduced_action_quantum_J_s must be positive and finite")
    return np.asarray(delta_action_J_s, dtype=float) / denom


def phase_from_specific_action(delta_specific_action_m2_s, reduced_specific_action_m2_s):
    """Return δφ = δs/(ħ/m) without requiring SI mass or a Planck target.

    [δs] = [ħ/m] = m^2 s^-1, hence δφ is dimensionless.
    """
    denom = float(reduced_specific_action_m2_s)
    if not np.isfinite(denom) or denom <= 0.0:
        raise ValueError("reduced_specific_action_m2_s must be positive and finite")
    return np.asarray(delta_specific_action_m2_s, dtype=float) / denom


def _as_kernel(kernel) -> np.ndarray:
    k = np.asarray(kernel, dtype=complex)
    if k.ndim == 1:
        k = k[None, :]
    if k.ndim != 2:
        raise ValueError("kernel must have shape (n_samples, n_integration_points)")
    if not np.all(np.isfinite(k.real)) or not np.all(np.isfinite(k.imag)):
        raise ValueError("kernel must be finite")
    return k


def _weights(weights, n_time: int) -> np.ndarray:
    w = np.asarray(weights, dtype=float)
    if w.ndim != 1 or len(w) != n_time:
        raise ValueError("weights must be a length-n_integration_points vector")
    if not np.all(np.isfinite(w)):
        raise ValueError("weights must be finite")
    return w


def discrete_amplitudes(kernel, weights, delta_phase) -> BridgeResult:
    """Evaluate the orthodox, exact-SST, and first-order amplitudes.

    The discretized orthodox kernel K0 already contains the dipole factor,
    XUV envelope and orthodox Volkov phase. The integration is

        M0 = Σ_j K0_j w_j
        M  = Σ_j K0_j exp(i δφ_j) w_j

    and, for |δφ| << 1,

        δM = i Σ_j K0_j δφ_j w_j.

    No assumption about the physical origin of δφ is made here.
    """
    k = _as_kernel(kernel)
    w = _weights(weights, k.shape[1])
    ph = np.asarray(delta_phase, dtype=float)
    if ph.ndim == 1:
        ph = ph[None, :]
    if ph.shape != k.shape:
        raise ValueError("delta_phase must have the same shape as kernel")
    if not np.all(np.isfinite(ph)):
        raise ValueError("delta_phase must be finite")

    kw = k * w[None, :]
    m0 = np.sum(kw, axis=1)
    m_exact = np.sum(kw * np.exp(1j * ph), axis=1)
    dm_linear = 1j * np.sum(kw * ph, axis=1)
    m_linear = m0 + dm_linear

    i0 = np.abs(m0) ** 2
    ie = np.abs(m_exact) ** 2
    # First-order intensity perturbation: 2 Re(M0* δM).
    di_linear = 2.0 * np.real(np.conjugate(m0) * dm_linear)
    return BridgeResult(
        amplitude_orthodox=m0,
        amplitude_exact=m_exact,
        amplitude_linear=m_linear,
        intensity_orthodox=i0,
        intensity_exact=ie,
        delta_intensity_exact=ie - i0,
        delta_intensity_linear=di_linear,
        phase=ph,
    )


def global_phase_null(kernel, weights, phase_rad: float = 0.731) -> dict[str, float | bool]:
    """Numerically enforce the factorable global-phase null theorem.

    If δφ_j = φ0 for every integration point j of a sample,
    M = exp(i φ0) M0 and |M|^2 = |M0|^2 exactly.
    """
    k = _as_kernel(kernel)
    ph = np.full(k.shape, float(phase_rad), dtype=float)
    r = discrete_amplitudes(k, weights, ph)
    scale = np.maximum(r.intensity_orthodox, 1e-300)
    rel = np.abs(r.intensity_exact - r.intensity_orthodox) / scale
    return {
        "max_relative_intensity_change": float(np.max(rel)),
        "mean_relative_intensity_change": float(np.mean(rel)),
        "pass_1e_12": bool(np.max(rel) <= 1e-12),
    }


def temporal_relative_phase(delta_phase, weights=None) -> dict[str, Any]:
    """Remove the unobservable per-sample constant phase and quantify what remains."""
    ph = np.asarray(delta_phase, dtype=float)
    if ph.ndim == 1:
        ph = ph[None, :]
    if ph.ndim != 2:
        raise ValueError("delta_phase must be 1D or 2D")
    if weights is None:
        w = np.ones(ph.shape[1], dtype=float)
    else:
        w = _weights(weights, ph.shape[1])
        w = np.abs(w)
    sw = float(np.sum(w))
    if sw <= 0.0:
        raise ValueError("absolute integration weights must have positive sum")
    means = np.sum(ph * w[None, :], axis=1) / sw
    rel = ph - means[:, None]
    rms = np.sqrt(np.sum(rel * rel * w[None, :], axis=1) / sw)
    return {
        "phase_global_component_rad": means,
        "phase_relative": rel,
        "relative_phase_rms_per_sample_rad": rms,
        "median_relative_phase_rms_rad": float(np.median(rms)),
        "max_relative_phase_rms_rad": float(np.max(rms)),
    }


def directional_asymmetry(intensity_plus, intensity_minus, eps: float = 1e-300):
    ip = np.asarray(intensity_plus, dtype=float)
    im = np.asarray(intensity_minus, dtype=float)
    if ip.shape != im.shape:
        raise ValueError("plus/minus intensity arrays must have identical shape")
    den = ip + im
    return (ip - im) / np.maximum(np.abs(den), eps)


def directional_residual(data_plus, data_minus, orthodox_plus, orthodox_minus):
    """Subtract the orthodox directional asymmetry before interpreting a residual."""
    a_data = directional_asymmetry(data_plus, data_minus)
    a_orth = directional_asymmetry(orthodox_plus, orthodox_minus)
    return a_data - a_orth


def sha256_arrays(**arrays) -> str:
    h = hashlib.sha256()
    for name in sorted(arrays):
        a = np.ascontiguousarray(np.asarray(arrays[name]))
        h.update(name.encode("utf-8"))
        h.update(str(a.shape).encode("ascii"))
        h.update(str(a.dtype).encode("ascii"))
        h.update(a.tobytes())
    return h.hexdigest()


def provenance_record(**kwargs) -> dict[str, Any]:
    rec = {
        "schema": "SST-ATTOS-VOLKOV-ACTION-BRIDGE-1.0",
        "free_phase_fit_parameters": 0,
        "planck_target_required_for_specific_action_path": False,
    }
    rec.update(kwargs)
    return rec
