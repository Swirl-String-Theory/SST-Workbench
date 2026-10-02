"""Spectral diagnostics and fail-closed admission for A048 observations.

Frequency extraction is not evidence of a new eigenbranch. In particular a
positive FFT bin from a short transient must not be promoted to a mode.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import coherence, welch


def _series(time, values):
    t, x = np.asarray(time, float), np.asarray(values, float)
    if t.ndim != 1 or x.shape != t.shape or len(t) < 8:
        raise ValueError("time and observable require equal one-dimensional arrays of length >= 8")
    if not (np.isfinite(t).all() and np.isfinite(x).all()):
        raise ValueError("nonfinite time or observable")
    dt = np.diff(t)
    if np.any(dt <= 0) or not np.allclose(dt, dt[0], rtol=1e-8, atol=1e-14):
        raise ValueError("strictly increasing uniformly sampled time required")
    return t, x, float(dt[0])


def spectrum(time, observable):
    t, x, dt = _series(time, observable)
    segment = min(256, max(8, len(t) // 4))
    f, power = welch(x, fs=1/dt, nperseg=segment, noverlap=segment//2, detrend="linear")
    # Spectral resolution is set by the segment duration, not the FFT array length.
    result = {"status": "INDETERMINATE", "evidence_scope": "observable_diagnostic",
              "frequency": f.tolist(), "angular_frequency": (2*np.pi*f).tolist(),
              "power": power.tolist(), "record_duration": float(t[-1]-t[0]),
              "segment_duration": segment*dt, "angular_resolution": float(2*np.pi/(segment*dt)),
              "measured_eigenfrequency": None,
              "reason": "A power spectrum alone does not establish stationarity, cycles, or an eigenmode."}
    return result


def leakage_diagnostic(time, centerline, material_phase):
    t, x, dt = _series(time, centerline)
    _, y, _ = _series(time, material_phase)
    if len(t) < 64:
        return {"status": "INDETERMINATE", "reason": "Insufficient samples for averaged coherence."}
    if np.var(x) <= np.finfo(float).tiny or np.var(y) <= np.finfo(float).tiny:
        return {"status": "INDETERMINATE", "reason": "Constant observable has undefined coherence."}
    nperseg = min(256, len(t)//4)
    f, c = coherence(x, y, fs=1/dt, nperseg=nperseg, noverlap=nperseg//2, detrend="linear")
    return {"status": "PASS", "evidence_scope": "coherence_estimator_only",
            "frequency": f.tolist(), "coherence": c.tolist(),
            "segment_samples": nperseg, "independent_nonoverlapping_segments": len(t)//nperseg,
            "interpretation": "High coherence is a leakage/coupling diagnostic; low coherence does not prove independence."}


REQUIRED_QUALIFICATION = (
    "independent_core_state", "active_material_perturbation", "material_observable",
    "centerline_observable", "spatial_convergence", "temporal_convergence",
    "core_resolution", "remesh_convergence", "topology", "invariants",
    "stationary_or_floquet_window", "amplitude_convergence", "frame_objectivity",
    "conventional_core_modes_null",
)


def branch_admission(producer):
    """Return an admission decision, never invent a physical model winner.

    A filament core smoothing parameter is not an independent core state.
    Even full Euler coefficients do not by themselves supply a measured phase.
    Ordinary Kelvin core/twist modes must be in H0 before any SST attribution.
    """
    gates = producer.get("qualification", {})
    reasons = [key for key in REQUIRED_QUALIFICATION if gates.get(key) != "PASS"]
    if producer.get("candidate_equation_drives_data", True):
        reasons.append("candidate_equation_independence_not_established")
    if producer.get("evidence_kind") != "INDEPENDENT_DYNAMICS":
        reasons.append("independent_dynamical_evidence_missing")
    if reasons:
        return {"status": "INDETERMINATE", "decision": "AMBIGUOUS",
                "physical_hypothesis": "NOT_YET_TESTED", "promotion_allowed": False,
                "missing_prerequisites": reasons, "model_competition_executed": False}
    return {"status": "NOT-IMPLEMENTED", "decision": "AMBIGUOUS",
            "physical_hypothesis": "NOT_YET_TESTED", "promotion_allowed": False,
            "missing_prerequisites": ["validated_joint_H0_H1_likelihood_and_holdout_competition"],
            "model_competition_executed": False}
