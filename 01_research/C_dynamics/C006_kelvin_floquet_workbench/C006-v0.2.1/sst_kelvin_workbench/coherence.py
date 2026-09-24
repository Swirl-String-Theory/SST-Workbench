from __future__ import annotations

import math
from collections import Counter
from typing import Iterable

import numpy as np


def _product_for_modes(series: dict[int, np.ndarray], modes: Iterable[int], conjugate: bool) -> np.ndarray:
    modes = list(int(m) for m in modes)
    if not modes:
        raise ValueError("at least one mode required")
    n = len(np.asarray(series[modes[0]]))
    out = np.ones(n, dtype=complex)
    for m in modes:
        a = np.asarray(series[m], dtype=complex)
        if len(a) != n:
            raise ValueError("all mode time series must have equal length")
        out *= np.conjugate(a) if conjugate else a
    return out


def normalized_wave_coherence(series: dict[int, np.ndarray], incoming: Iterable[int], outgoing: Iterable[int]) -> float:
    """General normalized N-wave phase coherence.

    P = |< prod(in)^* prod(out) >| / sqrt(<|prod(in)|^2><|prod(out)|^2>)
    """
    xin = _product_for_modes(series, incoming, conjugate=False)
    xout = _product_for_modes(series, outgoing, conjugate=False)
    num = abs(np.mean(np.conjugate(xin) * xout))
    den = math.sqrt(float(np.mean(np.abs(xin) ** 2) * np.mean(np.abs(xout) ** 2)))
    return float(num / max(den, 1e-300))


def combination_phase(series: dict[int, np.ndarray], incoming: Iterable[int], outgoing: Iterable[int]) -> np.ndarray:
    """Theta_N(t) = sum phi_in - sum phi_out, respecting repeated modes."""
    incoming = list(int(m) for m in incoming); outgoing = list(int(m) for m in outgoing)
    ref = np.asarray(series[incoming[0] if incoming else outgoing[0]], dtype=complex)
    theta = np.zeros(len(ref), dtype=float)
    for m in incoming:
        theta += np.unwrap(np.angle(np.asarray(series[m], dtype=complex)))
    for m in outgoing:
        theta -= np.unwrap(np.angle(np.asarray(series[m], dtype=complex)))
    return np.unwrap(theta)


def phase_lock_metrics(times: np.ndarray, theta: np.ndarray) -> dict[str, float]:
    t = np.asarray(times, dtype=float); th = np.asarray(theta, dtype=float)
    if len(t) != len(th) or len(t) < 4:
        raise ValueError("times/theta length mismatch or too short")
    p = np.polyfit(t, th, 1)
    resid = th - (p[0] * t + p[1])
    wrapped = np.angle(np.exp(1j * resid))
    return {
        "combination_phase_drift_hat": float(p[0]),
        "combination_phase_residual_rms_rad": float(np.sqrt(np.mean(resid * resid))),
        "phase_lock_resultant": float(abs(np.mean(np.exp(1j * wrapped)))),
    }


def modal_energy_proxy(series: dict[int, np.ndarray]) -> dict[int, np.ndarray]:
    return {int(m): (int(m) ** 2) * np.abs(np.asarray(a, dtype=complex)) ** 2 for m, a in series.items()}


def cumulative_transfer_flux_proxy(times: np.ndarray, series: dict[int, np.ndarray]) -> dict[int, float]:
    """Unforced redistribution diagnostic, not a stationary forced-cascade flux.

    Returns the time-averaged -d/dt of cumulative low-mode quadratic energy proxy.
    A plateau across mode cutoff is suggestive of conservative transfer but does not
    replace a forcing/dissipation-resolved flux derivation.
    """
    t = np.asarray(times, dtype=float)
    e = modal_energy_proxy(series)
    modes = sorted(e)
    out: dict[int, float] = {}
    cumulative = np.zeros_like(t)
    for m in modes:
        cumulative = cumulative + e[m]
        der = np.gradient(cumulative, t)
        # robust central 80% average to reduce endpoint/transient sensitivity
        lo = max(1, int(0.1 * len(t))); hi = max(lo + 1, int(0.9 * len(t)))
        out[m] = float(-np.mean(der[lo:hi]))
    return out


def instantaneous_frequency_stats(times: np.ndarray, z: np.ndarray) -> dict[str, float]:
    t = np.asarray(times, dtype=float); a = np.asarray(z, dtype=complex)
    ph = np.unwrap(np.angle(a))
    w = np.gradient(ph, t)
    amp = np.abs(a)
    mask = amp > max(0.1 * np.max(amp), 1e-14)
    if np.sum(mask) < 5:
        return {"omega_mean_hat": float("nan"), "delta_omega_hat": float("nan"), "tau_nl_hat": float("nan")}
    wm = float(np.mean(w[mask])); dw = float(np.std(w[mask]))
    return {
        "omega_mean_hat": wm,
        "delta_omega_hat": dw,
        "tau_nl_hat": float(1.0 / max(dw, 1e-30)),
    }
