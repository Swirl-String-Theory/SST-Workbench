from __future__ import annotations
import numpy as np


def kabsch_align(P, Q):
    P = np.asarray(P, float)
    Q = np.asarray(Q, float)
    Pc = P - P.mean(0)
    Qc = Q - Q.mean(0)
    H = Pc.T @ Qc
    U, S, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if np.linalg.det(R) < 0:
        Vt[-1] *= -1
        R = Vt.T @ U.T
    return Pc @ R


def aligned_displacement(snaps, base):
    base0 = np.asarray(base, float) - np.asarray(base, float).mean(0)
    out = []
    for X in np.asarray(snaps):
        out.append((kabsch_align(X, base) - base0).reshape(-1))
    return np.asarray(out)


def pod_freeze(odd, discovery_fraction=0.4):
    """Legacy split-discovery helper retained for validation/backward compatibility."""
    n = max(8, int(len(odd) * discovery_fraction))
    n = min(n, len(odd))
    D = np.asarray(odd, float)[:n]
    mu = D.mean(0)
    U, S, Vt = np.linalg.svd(D - mu, full_matrices=False)
    phi = Vt[0]
    coef = (np.asarray(odd, float) - mu) @ phi
    frac = float(S[0] ** 2 / max(np.sum(S * S), 1e-300))
    return phi, mu, coef, n, frac


def discover_pod_mode(odd, transient_fraction=0.10):
    """Discover one frozen shape-response direction in a dedicated probe run.

    The discovery run is separate from the action-amplitude runs.  The resulting
    mode is later projected into the local normal bundle and frozen before any
    matched energy/frequency measurements are made.
    """
    D = np.asarray(odd, float)
    if D.ndim != 2 or len(D) < 12:
        raise RuntimeError("insufficient snapshots for frozen-mode discovery")
    start = min(len(D) - 8, max(0, int(round(len(D) * float(transient_fraction)))))
    Q = D[start:]
    mu = Q.mean(0)
    U, S, Vt = np.linalg.svd(Q - mu, full_matrices=False)
    if len(S) == 0 or not np.isfinite(S[0]) or S[0] <= 0:
        raise RuntimeError("degenerate POD discovery")
    phi = Vt[0].copy()
    frac = float(S[0] ** 2 / max(np.sum(S * S), 1e-300))
    return phi, {
        "pod_power_fraction": frac,
        "discovery_start_index": int(start),
        "discovery_snapshots_used": int(len(Q)),
    }


def dominant_frequency(times, coef, start=0):
    t = np.asarray(times, float)[int(start):]
    a = np.asarray(coef, float)[int(start):]
    if len(t) < 16:
        return {
            "frequency": float("nan"),
            "omega": float("nan"),
            "spectral_power": 0.0,
            "cycles": 0.0,
            "period_cv": float("inf"),
            "harmonic_r2": 0.0,
            "fft_bin_index": -1,
            "frequency_window_limited": True,
            "holdout_duration": float(t[-1] - t[0]) if len(t) > 1 else 0.0,
            "fft_bin_width": float("inf"),
        }
    dt = float(np.median(np.diff(t)))
    if not np.isfinite(dt) or dt <= 0:
        raise RuntimeError("invalid sample spacing in frequency analysis")
    a = a - np.mean(a)
    win = np.hanning(len(a))
    Y = np.fft.rfft(a * win)
    f = np.fft.rfftfreq(len(a), dt)
    P = np.abs(Y) ** 2
    P[0] = 0
    i = int(np.argmax(P))
    freq = float(f[i])
    if 0 < i < len(P) - 1 and P[i - 1] > 0 and P[i] > 0 and P[i + 1] > 0:
        y0, y1, y2 = np.log(P[i - 1]), np.log(P[i]), np.log(P[i + 1])
        den = y0 - 2 * y1 + y2
        if abs(den) > 1e-15:
            delta = max(-0.5, min(0.5, 0.5 * (y0 - y2) / den))
            freq = float((i + delta) * (f[1] - f[0]))
    spec = float(P[i] / max(P.sum(), 1e-300))
    duration = float(t[-1] - t[0])
    cycles = float(freq * duration)

    A = np.column_stack([
        np.sin(2 * np.pi * freq * t),
        np.cos(2 * np.pi * freq * t),
        np.ones_like(t),
    ])
    q = np.linalg.lstsq(A, a, rcond=None)[0]
    pred = A @ q
    sst = np.sum((a - a.mean()) ** 2)
    r2 = float(1 - np.sum((a - pred) ** 2) / sst) if sst > 0 else 0.0

    z = np.where(np.diff(np.signbit(a)))[0]
    if len(z) >= 5:
        tz = t[z]
        periods = np.diff(tz[::2])
        pcv = float(np.std(periods) / np.mean(periods)) if len(periods) > 1 and np.mean(periods) > 0 else float("inf")
    else:
        pcv = float("inf")

    bin_width = float(f[1] - f[0]) if len(f) > 1 else float("inf")
    return {
        "frequency": freq,
        "omega": 2 * np.pi * freq,
        "spectral_power": spec,
        "cycles": cycles,
        "period_cv": pcv,
        "harmonic_r2": r2,
        "fft_bin_index": i,
        "frequency_window_limited": bool(i <= 1),
        "holdout_duration": duration,
        "fft_bin_width": bin_width,
    }
