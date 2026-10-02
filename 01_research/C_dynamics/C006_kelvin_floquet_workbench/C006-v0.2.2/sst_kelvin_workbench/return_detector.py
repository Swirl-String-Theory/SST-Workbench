"""Phase-blind return detector and unwrap frequency fit. Frozen before trajectories."""

from __future__ import annotations

from typing import Any

import numpy as np

from .paths import load_thresholds


def envelope_norm(delta: np.ndarray) -> np.ndarray:
    x = np.asarray(delta, dtype=float)
    if x.ndim == 3:
        return np.linalg.norm(x.reshape(x.shape[0], -1), axis=1)
    return np.linalg.norm(x, axis=tuple(range(1, x.ndim)))


def autocorrelation(E: np.ndarray) -> np.ndarray:
    e = np.asarray(E, dtype=float)
    n = e.size
    out = np.empty(n, dtype=float)
    e2 = float(np.dot(e, e))
    for lag in range(n):
        a = e[: n - lag]
        b = e[lag:]
        den = np.sqrt(np.dot(a, a) * np.dot(b, b))
        out[lag] = float(np.dot(a, b) / den) if den > 0 else 0.0
    if e2 <= 0:
        out[:] = 0.0
    return out


def first_qualified_local_max(tau, C, *, tau_min: float, tau_max: float, C_min: float) -> dict[str, Any]:
    tau = np.asarray(tau, dtype=float)
    C = np.asarray(C, dtype=float)
    hits = []
    for i in range(1, len(C) - 1):
        if not (tau_min <= tau[i] <= tau_max):
            continue
        if C[i] > C[i - 1] and C[i] >= C[i + 1] and C[i] >= C_min:
            denom = C[i - 1] - 2.0 * C[i] + C[i + 1]
            if abs(denom) > 1e-14:
                delta = 0.5 * (C[i - 1] - C[i + 1]) / denom
                delta = float(np.clip(delta, -1.0, 1.0))
            else:
                delta = 0.0
            dt = tau[i] - tau[i - 1] if i > 0 else 0.0
            hits.append({"index": i, "tau": float(tau[i] + delta * dt), "C": float(C[i])})
    if not hits:
        return {"found": False, "tau_return": float("nan"), "C": float("nan")}
    first = hits[0]
    return {"found": True, "tau_return": first["tau"], "C": first["C"], "n_qualified": len(hits)}


def unwrap_phase(a, *, amplitude_floor: float) -> dict[str, Any]:
    z = np.asarray(a, dtype=complex)
    amp = np.abs(z)
    mask = amp >= float(amplitude_floor)
    if int(np.sum(mask)) < 3:
        return {"ok": False, "phi": np.asarray([], dtype=float), "mask": mask}
    phi = np.unwrap(np.angle(z[mask]))
    return {"ok": True, "phi": phi, "t_index": np.nonzero(mask)[0], "mask": mask}


def fit_omega_td(t, phi) -> dict[str, Any]:
    t = np.asarray(t, dtype=float)
    phi = np.asarray(phi, dtype=float)
    if t.size < 3:
        return {"ok": False, "omega_td": float("nan")}
    A = np.column_stack((np.ones(t.size), t))
    coef, *_ = np.linalg.lstsq(A, phi, rcond=None)
    pred = A @ coef
    rms = float(np.sqrt(np.mean((phi - pred) ** 2)))
    return {"ok": True, "phi0": float(coef[0]), "omega_td": float(coef[1]), "rms": rms}


def detect_return(t, envelope, thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
    thr = (thresholds or load_thresholds())["detector"]
    t = np.asarray(t, dtype=float)
    C = autocorrelation(np.asarray(envelope, dtype=float))
    tau = t - t[0]
    rec = first_qualified_local_max(
        tau,
        C,
        tau_min=float(thr["tau_min_hat"]),
        tau_max=float(thr["tau_max_hat"]),
        C_min=float(thr["C_min"]),
    )
    rec["prediction_inputs_consumed"] = []
    rec["window"] = [float(thr["tau_min_hat"]), float(thr["tau_max_hat"])]
    rec["C_min"] = float(thr["C_min"])
    return rec


def trajectory_frequency(t, a, thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
    thr = (thresholds or load_thresholds())["detector"]
    z = np.asarray(a, dtype=complex)
    floor = float(thr["amplitude_floor_frac"]) * max(float(np.max(np.abs(z))), 1e-30)
    unw = unwrap_phase(z, amplitude_floor=floor)
    if not unw["ok"]:
        return {"ok": False, "omega_td": float("nan"), "prediction_inputs_consumed": []}
    t_fit = np.asarray(t, dtype=float)[unw["t_index"]]
    fit = fit_omega_td(t_fit, unw["phi"])
    fit["prediction_inputs_consumed"] = []
    fit["amplitude_floor"] = floor
    return fit
