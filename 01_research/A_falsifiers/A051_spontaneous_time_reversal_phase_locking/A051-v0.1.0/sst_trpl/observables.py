from __future__ import annotations
import numpy as np


def chi_t(eta: np.ndarray, eps: float = 1e-15) -> np.ndarray:
    """Gauge-invariant, normalized two-mode time-odd order parameter."""
    eta = np.asarray(eta)
    if eta.shape[-1] != 2:
        raise ValueError("eta last dimension must be 2")
    a, b = eta[..., 0], eta[..., 1]
    den = np.abs(a) ** 2 + np.abs(b) ** 2 + eps
    return 2.0 * np.imag(np.conjugate(a) * b) / den


def mode_weight(eta: np.ndarray, eps: float = 1e-15) -> np.ndarray:
    eta = np.asarray(eta)
    a, b = eta[..., 0], eta[..., 1]
    den = np.abs(a) ** 2 + np.abs(b) ** 2 + eps
    return 2.0 * np.abs(a) * np.abs(b) / den


def relative_phase(eta: np.ndarray) -> np.ndarray:
    eta = np.asarray(eta)
    return np.angle(eta[..., 1] * np.conjugate(eta[..., 0]))


def phase_lock_metrics(t: np.ndarray, eta: np.ndarray, burnin_fraction: float = 0.25, eps: float = 1e-15) -> dict:
    t = np.asarray(t, dtype=float)
    eta = np.asarray(eta)
    if eta.shape != (t.size, 2):
        raise ValueError("eta must have shape (nt,2)")
    i0 = min(max(int(round(burnin_fraction * t.size)), 0), max(t.size - 3, 0))
    tt = t[i0:]
    ee = eta[i0:]
    w = mode_weight(ee, eps)
    phi = relative_phase(ee)
    chi = chi_t(ee, eps)
    ws = float(np.sum(w))
    if not np.isfinite(ws) or ws <= eps:
        return {"status":"INSUFFICIENT_MODE_SUPPORT","mean_weight":0.0,"coherence":0.0,"chi_mean":0.0,"phase_mean":0.0,"phase_drift_per_window_rad":float("nan")}
    z = np.sum(w * np.exp(1j * phi)) / ws
    chi_mean = float(np.sum(w * chi) / ws)
    phase_mean = float(np.angle(z))
    coherence = float(np.abs(z))
    # unwrap about the circular mean before linear fit
    shifted = np.angle(np.exp(1j * (phi - phase_mean))) + phase_mean
    unwrapped = np.unwrap(shifted)
    if tt.size >= 3 and tt[-1] > tt[0]:
        slope = float(np.polyfit(tt - tt[0], unwrapped, 1)[0])
        drift = abs(slope) * float(tt[-1] - tt[0])
    else:
        drift = float("nan")
    return {
        "status":"OK","mean_weight":float(np.mean(w)),"coherence":coherence,
        "chi_mean":chi_mean,"phase_mean":phase_mean,"phase_drift_per_window_rad":drift,
        "samples":int(tt.size)
    }


def gauge_rotate(eta: np.ndarray, theta: float) -> np.ndarray:
    return np.asarray(eta) * np.exp(1j * float(theta))


def time_reverse_conjugate(eta: np.ndarray) -> np.ndarray:
    """Default representation-level antiunitary map; producer must certify applicability."""
    return np.conjugate(np.asarray(eta))
