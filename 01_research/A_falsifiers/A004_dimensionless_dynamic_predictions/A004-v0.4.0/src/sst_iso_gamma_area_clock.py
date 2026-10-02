#!/usr/bin/env python3
"""Iso-Gamma/A dynamic-clock falsification campaign for SST research track.

This module tests the hypothesis

    omega_clock = (Gamma / A) / 2

without using that formula to *measure* the dynamic period.  The measured
quantity is extracted from the evolving trefoil geometry through the phase of
an independently observed complex multipole moment.  A matched isolated run is
subtracted to remove the trefoil's self-induced laboratory-frame rotation.

Primary falsifier
-----------------
For a prescribed mean vorticity zeta_bar = Gamma/A, define

    omega_pred = zeta_bar / 2,
    omega_bg_obs = omega_bundle_obs - omega_isolated_obs,
    Q_Gamma = omega_bg_obs / omega_pred.

The hypothesis predicts Q_Gamma = 1 for every member of an iso-Gamma/A family,
independent of bundle area.  A certified value outside the preregistered
interval, or excessive spread across equal-zeta configurations, falsifies the
claim within the frozen straight-bundle model.

The background tubes remain frozen and straight.  This package does not claim
full 3-D mutual backreaction or an emergent proper-time theorem.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from sst_dimensionless_ratios import (
    CurveSource,
    NumericalProtocol,
    best_cyclic_recurrence,
    biot_savart_velocity,
    curve_length,
    discrete_curvature,
    load_curve,
    normalize_curve,
    self_induction_energy_proxy,
    uniform_arclength_resample,
)
from sst_axial_vortex_bundle import (
    BundleProtocol,
    _axis_basis,
    _rk4,
    _unit,
    bundle_velocity,
    central_aperture,
    resolve_bundle,
)

Array = np.ndarray
TAU = 2.0 * math.pi
SCHEMA_VERSION = "0.4.0"


@dataclass(frozen=True)
class DynamicClockProtocol:
    phase_harmonic: int = 3
    target_predicted_cycles: float = 4.5
    burn_in_predicted_cycles: float = 0.5
    dt: float = 5.0e-4
    sample_every: int = 10
    remesh_every: int = 1
    remove_tangential: bool = True
    min_measured_cycles: float = 3.0
    phase_r2_min: float = 0.98
    initial_fit_predicted_cycles: float = 0.25
    initial_fit_time: float | None = None
    initial_phase_r2_min: float = 0.995
    initial_fit_min_samples: int = 5
    phase_amplitude_min: float = 1.0e-3
    delta_omega_snr_min: float = 5.0
    q_tolerance: float = 0.02
    iso_family_spread_tolerance: float = 0.02
    shape_clock_enabled: bool = True
    shape_min_cycles: float = 3.0
    shape_snr_min: float = 5.0
    shape_autocorr_min: float = 0.30
    shape_period_agreement: float = 0.15
    save_timeseries: bool = True
    compute_recurrence: bool = False


def _source(d: Mapping[str, Any]) -> CurveSource:
    return CurveSource(
        knot_id=str(d["knot_id"]),
        label=str(d.get("label", d["knot_id"])),
        source=str(d.get("source", "ideal_ab")),
        generator=d.get("generator"),
        mirror=bool(d.get("mirror", False)),
    )


def _parse_vec(value: Any, default: tuple[float, float, float]) -> tuple[float, float, float]:
    if value is None:
        return default
    if isinstance(value, str):
        value = [float(x.strip()) for x in value.split(",")]
    if len(value) != 3:
        raise ValueError("expected a 3-vector")
    return tuple(float(x) for x in value)


def _load_config(path: str | Path) -> dict[str, Any]:
    p = Path(path).resolve()
    cfg = json.loads(p.read_text(encoding="utf-8"))
    if cfg.get("ideal_file"):
        candidate = Path(cfg["ideal_file"])
        if not candidate.is_absolute():
            cfg["ideal_file"] = str((p.parent / candidate).resolve())
    return cfg


def _base_protocol(config: Mapping[str, Any], resolution: int, epsilon: float, kernel: str) -> NumericalProtocol:
    return NumericalProtocol(
        resolution=int(resolution),
        epsilon=float(epsilon),
        kernel=str(kernel),
        circulation=float(config.get("circulation", 1.0)),
        normalization=str(config.get("normalization", "fixed_sampled_reach")),
        target_length=float(config.get("target_length", TAU)),
        neighbor_skip=config.get("neighbor_skip"),
    )


def _dynamic_protocol(config: Mapping[str, Any]) -> DynamicClockProtocol:
    d = config.get("dynamic_clock", {}) or {}
    kwargs = {}
    for name in DynamicClockProtocol.__dataclass_fields__:
        if name in d:
            kwargs[name] = d[name]
    return DynamicClockProtocol(**kwargs)


def _centred_transverse_complex(points: Array, axis: Sequence[float]) -> Array:
    p = np.asarray(points, dtype=float)
    p = p - np.mean(p, axis=0, keepdims=True)
    ahat = _unit(axis)
    e1, e2 = _axis_basis(ahat)
    return (p @ e1) + 1j * (p @ e2)


def complex_shape_multipole(points: Array, axis: Sequence[float], harmonic: int) -> complex:
    if harmonic < 1:
        raise ValueError("phase_harmonic must be >= 1")
    z = _centred_transverse_complex(points, axis)
    scale = float(np.sqrt(np.mean(np.abs(z) ** 2)))
    if scale <= 1e-15:
        return 0j
    return complex(np.mean((z / scale) ** harmonic))


def shape_observables(points: Array, axis: Sequence[float]) -> dict[str, float]:
    p = np.asarray(points, dtype=float)
    kappa, ds = discrete_curvature(p)
    kmean = float(np.average(kappa, weights=ds))
    krms = float(np.sqrt(np.average(kappa * kappa, weights=ds)))
    kstd = float(np.sqrt(max(krms * krms - kmean * kmean, 0.0)))
    curvature_cv = kstd / max(abs(kmean), 1e-15)
    bending = float(np.sum(kappa * kappa * ds))

    centred = p - np.mean(p, axis=0, keepdims=True)
    cov = centred.T @ centred / max(len(centred), 1)
    eig = np.sort(np.linalg.eigvalsh(cov))
    anisotropy = float((eig[-1] - eig[0]) / max(float(np.sum(eig)), 1e-15))

    ahat = _unit(axis)
    axial = centred @ ahat
    axial_rms = float(np.sqrt(np.mean(axial * axial)))
    transverse = centred - np.outer(axial, ahat)
    transverse_rms = float(np.sqrt(np.mean(np.sum(transverse * transverse, axis=1))))
    aspect = axial_rms / max(transverse_rms, 1e-15)
    return {
        "curvature_cv": curvature_cv,
        "bending_integral": bending,
        "inertia_anisotropy": anisotropy,
        "axial_transverse_aspect": aspect,
    }


def _linear_fit_with_error(t: Array, y: Array) -> dict[str, float | int | str]:
    t = np.asarray(t, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(t) < 4 or not np.isfinite(t).all() or not np.isfinite(y).all():
        return {"status": "INSUFFICIENT_DATA", "slope": math.nan, "intercept": math.nan,
                "r2": math.nan, "slope_stderr": math.inf, "samples": int(len(t))}
    x = t - float(np.mean(t))
    sxx = float(np.dot(x, x))
    if sxx <= 1e-30:
        return {"status": "DEGENERATE_TIME_GRID", "slope": math.nan, "intercept": math.nan,
                "r2": math.nan, "slope_stderr": math.inf, "samples": int(len(t))}
    slope = float(np.dot(x, y - float(np.mean(y))) / sxx)
    intercept = float(np.mean(y) - slope * np.mean(t))
    fitted = slope * t + intercept
    residual = y - fitted
    ss_res = float(np.dot(residual, residual))
    ss_tot = float(np.dot(y - float(np.mean(y)), y - float(np.mean(y))))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-30 else 1.0
    dof = max(len(t) - 2, 1)
    sigma2 = ss_res / dof
    slope_stderr = float(math.sqrt(max(sigma2 / sxx, 0.0)))
    return {
        "status": "FIT_OK",
        "slope": slope,
        "intercept": intercept,
        "r2": r2,
        "slope_stderr": slope_stderr,
        "samples": int(len(t)),
    }


def extract_initial_phase_rate(
    times: Sequence[float],
    multipoles: Sequence[complex],
    protocol: DynamicClockProtocol,
    predicted_period: float,
) -> dict[str, Any]:
    """Fit the initial geometric phase rate over a preregistered short window.

    This is the primary instantaneous clock-rate falsifier.  It does not require
    a complete cycle because the directly observed complex phase is regressed,
    rather than inferred from a spectral peak.  The strict multi-cycle period
    fit remains a separate secondary gate.
    """
    t = np.asarray(times, dtype=float)
    m = np.asarray(multipoles, dtype=complex)
    amp = np.abs(m)
    orientation_phase = np.unwrap(np.angle(m)) / float(protocol.phase_harmonic)
    end_time = (
        float(protocol.initial_fit_time)
        if protocol.initial_fit_time is not None
        else protocol.initial_fit_predicted_cycles * predicted_period
    )
    mask = (
        (t <= end_time + 1e-15)
        & np.isfinite(orientation_phase)
        & (amp >= protocol.phase_amplitude_min)
    )
    fit = _linear_fit_with_error(t[mask], orientation_phase[mask])
    reasons: list[str] = []
    if int(np.count_nonzero(mask)) < protocol.initial_fit_min_samples:
        reasons.append("TOO_FEW_INITIAL_SAMPLES")
    if fit.get("status") != "FIT_OK":
        reasons.append(str(fit.get("status")))
    else:
        if float(fit.get("r2", -math.inf)) < protocol.initial_phase_r2_min:
            reasons.append("INITIAL_PHASE_NONLINEAR")
        if float(np.min(amp[mask])) < protocol.phase_amplitude_min:
            reasons.append("MULTIPOLE_AMPLITUDE_COLLAPSE")
    slope = float(fit.get("slope", math.nan))
    span = 0.0
    if np.count_nonzero(mask) >= 2:
        ph = orientation_phase[mask]
        span = float(abs(ph[-1] - ph[0]) / TAU)
    return {
        **fit,
        "certified": not reasons,
        "certification_reason": "PASS" if not reasons else ";".join(dict.fromkeys(reasons)),
        "fit_end_time": float(end_time),
        "phase_span_cycles": span,
        "period_extrapolated": TAU / abs(slope) if math.isfinite(slope) and abs(slope) > 1e-15 else None,
        "mean_amplitude": float(np.mean(amp[mask])) if np.count_nonzero(mask) else 0.0,
        "minimum_amplitude": float(np.min(amp[mask])) if np.count_nonzero(mask) else 0.0,
    }


def extract_orientation_phase(
    times: Sequence[float],
    multipoles: Sequence[complex],
    protocol: DynamicClockProtocol,
    predicted_period: float,
) -> dict[str, Any]:
    t = np.asarray(times, dtype=float)
    m = np.asarray(multipoles, dtype=complex)
    amp = np.abs(m)
    raw_phase = np.angle(m)
    orientation_phase = np.unwrap(raw_phase) / float(protocol.phase_harmonic)
    burn_time = protocol.burn_in_predicted_cycles * predicted_period
    mask = (t >= burn_time) & np.isfinite(orientation_phase) & (amp >= protocol.phase_amplitude_min)
    fit = _linear_fit_with_error(t[mask], orientation_phase[mask])
    if fit["status"] != "FIT_OK":
        return {
            **fit,
            "certified": False,
            "certification_reason": fit["status"],
            "mean_amplitude": float(np.mean(amp)) if len(amp) else 0.0,
            "minimum_amplitude": float(np.min(amp)) if len(amp) else 0.0,
            "measured_cycles": 0.0,
            "period": None,
        }
    slope = float(fit["slope"])
    used_t = t[mask]
    span = float(used_t[-1] - used_t[0]) if len(used_t) > 1 else 0.0
    cycles = abs(slope) * span / TAU
    period = TAU / abs(slope) if abs(slope) > 1e-15 else None
    reasons: list[str] = []
    if float(fit["r2"]) < protocol.phase_r2_min:
        reasons.append("PHASE_NONLINEAR")
    if cycles < protocol.min_measured_cycles:
        reasons.append("TOO_FEW_PHASE_CYCLES")
    if float(np.min(amp[mask])) < protocol.phase_amplitude_min:
        reasons.append("MULTIPOLE_AMPLITUDE_COLLAPSE")
    return {
        **fit,
        "certified": not reasons,
        "certification_reason": "PASS" if not reasons else ";".join(reasons),
        "mean_amplitude": float(np.mean(amp[mask])),
        "minimum_amplitude": float(np.min(amp[mask])),
        "measured_cycles": float(cycles),
        "period": period,
    }


def _detrend_linear(t: Array, y: Array) -> Array:
    fit = _linear_fit_with_error(t, y)
    if fit["status"] != "FIT_OK":
        return y - float(np.mean(y))
    return y - (float(fit["slope"]) * t + float(fit["intercept"]))


def extract_scalar_period(
    times: Sequence[float],
    values: Sequence[float],
    protocol: DynamicClockProtocol,
) -> dict[str, Any]:
    t = np.asarray(times, dtype=float)
    y = np.asarray(values, dtype=float)
    if len(t) < 16 or len(t) != len(y):
        return {"status": "INSUFFICIENT_DATA", "certified": False, "period": None}
    dt = float(np.median(np.diff(t)))
    duration = float(t[-1] - t[0])
    if dt <= 0 or duration <= 0:
        return {"status": "INVALID_TIME_GRID", "certified": False, "period": None}
    x = _detrend_linear(t, y)
    scale = float(np.std(x))
    if scale <= 1e-14:
        return {"status": "NO_SHAPE_OSCILLATION", "certified": False, "period": None}
    window = np.hanning(len(x))
    spec = np.fft.rfft(x * window)
    freq = np.fft.rfftfreq(len(x), d=dt)
    power = np.abs(spec) ** 2
    min_freq = protocol.shape_min_cycles / duration
    valid = (freq >= min_freq) & (freq > 0)
    if not np.any(valid):
        return {"status": "NO_ELIGIBLE_FREQUENCY", "certified": False, "period": None}
    indices = np.flatnonzero(valid)
    peak_idx = int(indices[np.argmax(power[valid])])
    peak_power = float(power[peak_idx])
    noise = float(np.median(power[valid]))
    snr = peak_power / max(noise, 1e-30)
    f_peak = float(freq[peak_idx])
    period_fft = 1.0 / f_peak
    cycles = duration / period_fft

    ac = np.correlate(x, x, mode="full")[len(x)-1:]
    ac /= max(float(ac[0]), 1e-30)
    lag0 = max(1, int(round(period_fft / dt)))
    lo = max(1, int(math.floor(0.75 * lag0)))
    hi = min(len(ac) - 1, int(math.ceil(1.25 * lag0)))
    if hi <= lo:
        return {"status": "AUTOCORR_WINDOW_INVALID", "certified": False, "period": period_fft}
    lag = lo + int(np.argmax(ac[lo:hi+1]))
    period_ac = lag * dt
    ac_peak = float(ac[lag])
    agreement = abs(period_ac - period_fft) / max(period_fft, 1e-30)
    reasons: list[str] = []
    if snr < protocol.shape_snr_min:
        reasons.append("LOW_SPECTRAL_SNR")
    if cycles < protocol.shape_min_cycles:
        reasons.append("TOO_FEW_SHAPE_CYCLES")
    if ac_peak < protocol.shape_autocorr_min:
        reasons.append("LOW_AUTOCORRELATION_PEAK")
    if agreement > protocol.shape_period_agreement:
        reasons.append("FFT_AUTOCORR_DISAGREE")
    period = 0.5 * (period_fft + period_ac)
    return {
        "status": "PASS" if not reasons else ";".join(reasons),
        "certified": not reasons,
        "period": float(period),
        "period_fft": float(period_fft),
        "period_autocorr": float(period_ac),
        "spectral_snr": float(snr),
        "autocorr_peak": float(ac_peak),
        "period_relative_disagreement": float(agreement),
        "measured_cycles": float(duration / period),
    }


def extract_shape_clock(times: Sequence[float], observables: Mapping[str, Sequence[float]], protocol: DynamicClockProtocol) -> dict[str, Any]:
    if not protocol.shape_clock_enabled:
        return {"status": "DISABLED", "certified": False, "period": None, "observables": {}}
    results = {name: extract_scalar_period(times, values, protocol) for name, values in observables.items()}
    periods = [float(r["period"]) for r in results.values() if r.get("certified") and r.get("period")]
    if len(periods) < 2:
        return {
            "status": "INSUFFICIENT_CROSS_OBSERVABLE_CONSENSUS",
            "certified": False,
            "period": None,
            "observables": results,
        }
    mean_period = float(np.mean(periods))
    spread = float((max(periods) - min(periods)) / max(mean_period, 1e-30))
    certified = spread <= protocol.shape_period_agreement
    return {
        "status": "PASS" if certified else "CROSS_OBSERVABLE_PERIOD_SPREAD",
        "certified": certified,
        "period": mean_period if certified else None,
        "relative_spread": spread,
        "certified_observable_count": len(periods),
        "observables": results,
    }


def _sample_state(
    points: Array,
    axis: Sequence[float],
    harmonic: int,
    initial: Array,
    compute_recurrence: bool,
) -> dict[str, Any]:
    obs = shape_observables(points, axis)
    multipole = complex_shape_multipole(points, axis, harmonic)
    out: dict[str, Any] = {
        **obs,
        "multipole_real": float(multipole.real),
        "multipole_imag": float(multipole.imag),
        "multipole_amplitude": float(abs(multipole)),
        "multipole_phase": float(np.angle(multipole)),
        "length": float(curve_length(points)),
    }
    if compute_recurrence:
        out["recurrence_error"] = float(best_cyclic_recurrence(initial, points, allow_reverse=False)["normalized_rmsd"])
    return out


def evolve_observed(
    initial_points: Array,
    base: NumericalProtocol,
    bundle: BundleProtocol,
    protocol: DynamicClockProtocol,
    predicted_period: float,
) -> tuple[dict[str, Any], dict[str, Array]]:
    p = np.asarray(initial_points, dtype=float).copy()
    initial = p.copy()
    resolved = resolve_bundle(initial, base.epsilon, bundle)
    duration = (protocol.target_predicted_cycles + protocol.burn_in_predicted_cycles) * predicted_period
    steps = max(1, int(math.ceil(duration / protocol.dt)))
    sample_every = max(1, int(protocol.sample_every))

    times: list[float] = []
    multipoles: list[complex] = []
    series: dict[str, list[float]] = {
        "curvature_cv": [],
        "bending_integral": [],
        "inertia_anisotropy": [],
        "axial_transverse_aspect": [],
        "length": [],
        "energy": [],
    }
    if protocol.compute_recurrence:
        series["recurrence_error"] = []

    e0 = float(self_induction_energy_proxy(p, base.epsilon, base.circulation))
    l0 = float(curve_length(p))

    def sample(step: int) -> None:
        t = step * protocol.dt
        state = _sample_state(p, bundle.axis, protocol.phase_harmonic, initial, protocol.compute_recurrence)
        times.append(float(t))
        multipoles.append(complex(state["multipole_real"], state["multipole_imag"]))
        for name in series:
            if name == "energy":
                series[name].append(float(self_induction_energy_proxy(p, base.epsilon, base.circulation)))
            else:
                series[name].append(float(state[name]))

    sample(0)
    for step in range(1, steps + 1):
        p = _rk4(p, protocol.dt, base, resolved, protocol.remove_tangential)
        if protocol.remesh_every > 0 and step % protocol.remesh_every == 0:
            p = uniform_arclength_resample(p, base.resolution)
        if step % sample_every == 0 or step == steps:
            sample(step)

    initial_phase_fit = extract_initial_phase_rate(times, multipoles, protocol, predicted_period)
    phase_fit = extract_orientation_phase(times, multipoles, protocol, predicted_period)
    shape_clock = extract_shape_clock(
        times,
        {k: v for k, v in series.items() if k in {
            "curvature_cv", "bending_integral", "inertia_anisotropy", "axial_transverse_aspect"
        }},
        protocol,
    )
    summary = {
        "status": "COMPLETE_FROZEN_BUNDLE",
        "steps": steps,
        "samples": len(times),
        "duration": float(times[-1]),
        "phase_harmonic": protocol.phase_harmonic,
        "initial_phase_fit": initial_phase_fit,
        "orientation_phase_fit": phase_fit,
        "shape_clock": shape_clock,
        "relative_energy_drift": float((series["energy"][-1] - e0) / max(abs(e0), 1e-15)),
        "relative_length_drift": float((series["length"][-1] - l0) / max(abs(l0), 1e-15)),
        "resolved_bundle": resolved.to_dict(),
    }
    arrays: dict[str, Array] = {
        "times": np.asarray(times, dtype=float),
        "multipole_real": np.asarray([z.real for z in multipoles], dtype=float),
        "multipole_imag": np.asarray([z.imag for z in multipoles], dtype=float),
    }
    arrays.update({name: np.asarray(values, dtype=float) for name, values in series.items()})
    return summary, arrays


def _safe_name(text: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in text)


def _representation_protocols(
    initial: Array,
    base: NumericalProtocol,
    axis: tuple[float, float, float],
    center: tuple[float, float, float],
    radius_ratio: float,
    signed_mean_vorticity: float,
    config: Mapping[str, Any],
) -> list[tuple[str, BundleProtocol]]:
    iso = config.get("iso_gamma_area", {}) or {}
    representations = [str(x) for x in iso.get("representations", ["continuum"])]
    require_inside = bool(iso.get("require_bundle_inside_hole", True))
    common = dict(
        axis=axis,
        center=center,
        radius_ratio_to_hole=float(radius_ratio),
        circulation_sign=1.0 if signed_mean_vorticity >= 0 else -1.0,
        frozen_tubes=True,
        require_bundle_inside_hole=require_inside,
        provenance="iso_gamma_area_preregistered",
        ladder_gate="C9_ISO_GAMMA_AREA_DYNAMIC_CLOCK",
    )
    out: list[tuple[str, BundleProtocol]] = []
    if "continuum" in representations:
        out.append(("continuum", BundleProtocol(
            kind="continuum_rankine",
            mode="continuum",
            strength_basis="mean_vorticity",
            mean_vorticity=abs(float(signed_mean_vorticity)),
            **common,
        )))

    if "numerical_discretization" in representations:
        centerline, free_hole = central_aperture(initial, axis, center, base.epsilon)
        radius = float(radius_ratio) * free_hole
        total = abs(float(signed_mean_vorticity)) * math.pi * radius * radius
        for n in [int(x) for x in iso.get("tube_counts", [19, 37, 61])]:
            out.append((f"numerical_N{n}", BundleProtocol(
                kind="discrete_axial_tubes",
                mode="numerical_discretization",
                total_circulation=total,
                tube_count=n,
                tube_kernel=str(iso.get("tube_kernel", "rankine")),
                packing_fraction=float(iso.get("packing_fraction", 0.25)),
                **common,
            )))
    return out


def _flatten_result(row: Mapping[str, Any]) -> dict[str, Any]:
    bundle = row["bundle_run"]["resolved_bundle"]
    phase = row["bundle_run"]["orientation_phase_fit"]
    baseline_phase = row["baseline_run"]["orientation_phase_fit"]
    initial_phase = row["bundle_run"]["initial_phase_fit"]
    baseline_initial_phase = row["baseline_run"]["initial_phase_fit"]
    shape = row["bundle_run"]["shape_clock"]
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": row["run_id"],
        "family_id": row["family_id"],
        "label": row["label"],
        "knot_id": row["knot_id"],
        "mirror": row["mirror"],
        "resolution": row["base_protocol"]["resolution"],
        "epsilon": row["base_protocol"]["epsilon"],
        "kernel": row["base_protocol"]["kernel"],
        "representation": row["representation"],
        "radius_ratio_to_hole": bundle["protocol"]["radius_ratio_to_hole"],
        "free_hole_radius": bundle["free_hole_radius"],
        "bundle_radius": bundle["bundle_radius"],
        "bundle_area": math.pi * bundle["bundle_radius"] ** 2,
        "tube_count": bundle["tube_count"],
        "total_circulation": bundle["total_circulation"],
        "mean_vorticity": bundle["mean_vorticity"],
        "gamma_over_area": row["gamma_over_area"],
        "predicted_omega": row["predicted_omega"],
        "predicted_period": row["predicted_period"],
        "baseline_omega_observed": baseline_phase.get("slope"),
        "bundle_omega_observed": phase.get("slope"),
        "initial_baseline_omega_observed": baseline_initial_phase.get("slope"),
        "initial_bundle_omega_observed": initial_phase.get("slope"),
        "initial_background_omega_observed": row["initial_background_omega_observed"],
        "initial_background_omega_stderr": row["initial_background_omega_stderr"],
        "initial_delta_omega_snr": row["initial_delta_omega_snr"],
        "t_dyn": row["t_dyn"],
        "q_gamma_signed": row["q_gamma_signed"],
        "q_gamma_abs": row["q_gamma_abs"],
        "q_gamma_stderr": row["q_gamma_stderr"],
        "strict_background_omega_observed": row["strict_background_omega_observed"],
        "strict_t_dyn": row["strict_t_dyn"],
        "strict_q_gamma_signed": row["strict_q_gamma_signed"],
        "initial_phase_fit_r2": initial_phase.get("r2"),
        "initial_baseline_phase_fit_r2": baseline_initial_phase.get("r2"),
        "initial_phase_span_cycles": initial_phase.get("phase_span_cycles"),
        "phase_fit_r2": phase.get("r2"),
        "baseline_phase_fit_r2": baseline_phase.get("r2"),
        "measured_phase_cycles": phase.get("measured_cycles"),
        "multipole_mean_amplitude": phase.get("mean_amplitude"),
        "initial_phase_fit_certified": initial_phase.get("certified"),
        "initial_baseline_fit_certified": baseline_initial_phase.get("certified"),
        "phase_fit_certified": phase.get("certified"),
        "baseline_fit_valid": row["baseline_fit_valid"],
        "t_dyn_certified": row["t_dyn_certified"],
        "t_dyn_certification_reason": row["t_dyn_certification_reason"],
        "hypothesis_run_pass": row["hypothesis_run_pass"],
        "shape_clock_certified": shape.get("certified"),
        "shape_period": shape.get("period"),
        "relative_energy_drift": row["bundle_run"]["relative_energy_drift"],
        "relative_length_drift": row["bundle_run"]["relative_length_drift"],
        "timeseries_file": row.get("timeseries_file"),
    }


def run_campaign(config: Mapping[str, Any], output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    timeseries_dir = output / "timeseries"
    timeseries_dir.mkdir(exist_ok=True)

    ideal_file = config.get("ideal_file")
    sources = [_source(x) for x in config.get("cases", [])]
    if not sources:
        sources = [CurveSource("3:1:1", "trefoil", "ideal_ab")]
    resolutions = [int(x) for x in config.get("resolutions", [64])]
    epsilons = [float(x) for x in config.get("epsilons", [0.05])]
    kernels = [str(x) for x in config.get("kernels", ["rosenhead"])]
    dynamic = _dynamic_protocol(config)
    iso = config.get("iso_gamma_area", {}) or {}
    mean_vorticities = [abs(float(x)) for x in iso.get("mean_vorticities", [32.0])]
    radius_ratios = [float(x) for x in iso.get("radius_ratios", [0.5, 0.9])]
    signs = [1.0 if float(x) >= 0 else -1.0 for x in iso.get("circulation_signs", [-1, 1])]
    axis = _parse_vec(iso.get("axis"), (0.0, 0.0, 1.0))
    center = _parse_vec(iso.get("center"), (0.0, 0.0, 0.0))

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "epistemic_status": "RESEARCH_TRACK_ISO_GAMMA_AREA_DYNAMIC_CLOCK_FALSIFIER",
        "claim_guard": (
            "T_dyn is measured from the evolving trefoil multipole phase and not copied from Gamma/A. "
            "The matched isolated phase rate is subtracted. Frozen straight background tubes only; "
            "no proper-time theorem or full 3-D backreaction is claimed."
        ),
        "hypothesis": "2*(omega_bundle_obs-omega_isolated_obs)/(Gamma/A) = 1",
        "config": dict(config),
        "rows": [],
    }

    baseline_cache: dict[tuple[Any, ...], tuple[dict[str, Any], dict[str, Array]]] = {}
    row_counter = 0
    for source in sources:
        for resolution in resolutions:
            for epsilon in epsilons:
                for kernel in kernels:
                    base = _base_protocol(config, resolution, epsilon, kernel)
                    raw = load_curve(source, max(resolution * 4, 512), ideal_file)
                    p0 = uniform_arclength_resample(raw, resolution)
                    p0 = normalize_curve(
                        p0,
                        base.normalization,
                        target_length=base.target_length,
                        target_reach=float(config.get("target_reach", 0.2)),
                        neighbor_skip=base.neighbor_skip,
                    )
                    p0 = uniform_arclength_resample(p0, resolution)

                    for zeta_abs in mean_vorticities:
                        predicted_period = 4.0 * math.pi / zeta_abs
                        baseline_key = (
                            source.knot_id, source.label, source.mirror,
                            resolution, epsilon, kernel, zeta_abs,
                            dynamic.phase_harmonic, dynamic.dt,
                            dynamic.target_predicted_cycles,
                            dynamic.burn_in_predicted_cycles,
                        )
                        if baseline_key not in baseline_cache:
                            baseline_bundle = BundleProtocol(
                                kind="none", mode="none", axis=axis, center=center,
                                ladder_gate="C9_ISO_GAMMA_AREA_BASELINE",
                            )
                            baseline_cache[baseline_key] = evolve_observed(
                                p0, base, baseline_bundle, dynamic, predicted_period
                            )
                        baseline_summary, baseline_arrays = baseline_cache[baseline_key]
                        baseline_phase = baseline_summary["orientation_phase_fit"]
                        baseline_initial_phase = baseline_summary["initial_phase_fit"]
                        baseline_fit_valid = bool(baseline_initial_phase.get("certified", False))

                        for sign in signs:
                            signed_zeta = sign * zeta_abs
                            for radius_ratio in radius_ratios:
                                reps = _representation_protocols(
                                    p0, base, axis, center, radius_ratio, signed_zeta, config
                                )
                                for representation, bundle in reps:
                                    bundle_summary, bundle_arrays = evolve_observed(
                                        p0, base, bundle, dynamic, predicted_period
                                    )
                                    phase = bundle_summary["orientation_phase_fit"]
                                    initial_phase = bundle_summary["initial_phase_fit"]
                                    predicted_omega = 0.5 * signed_zeta

                                    # Primary, independently measured instantaneous phase-rate falsifier.
                                    initial_omega_bundle = float(initial_phase.get("slope", math.nan))
                                    initial_omega_baseline = float(baseline_initial_phase.get("slope", math.nan))
                                    initial_delta = initial_omega_bundle - initial_omega_baseline
                                    initial_se = math.sqrt(
                                        float(initial_phase.get("slope_stderr", math.inf)) ** 2
                                        + float(baseline_initial_phase.get("slope_stderr", math.inf)) ** 2
                                    )
                                    q_signed = initial_delta / predicted_omega if abs(predicted_omega) > 1e-15 else math.nan
                                    q_abs = abs(q_signed) if math.isfinite(q_signed) else math.nan
                                    q_stderr = initial_se / abs(predicted_omega) if abs(predicted_omega) > 1e-15 else math.inf
                                    initial_delta_snr = abs(initial_delta) / max(initial_se, 1e-30)
                                    t_dyn = TAU / abs(initial_delta) if abs(initial_delta) > 1e-15 else None

                                    # Secondary strict multi-cycle estimate; it may remain uncertified.
                                    strict_omega_bundle = float(phase.get("slope", math.nan))
                                    strict_omega_baseline = float(baseline_phase.get("slope", math.nan))
                                    strict_delta = strict_omega_bundle - strict_omega_baseline
                                    strict_q = strict_delta / predicted_omega if abs(predicted_omega) > 1e-15 else math.nan
                                    strict_t_dyn = TAU / abs(strict_delta) if abs(strict_delta) > 1e-15 else None

                                    reasons: list[str] = []
                                    if not baseline_fit_valid:
                                        reasons.append("BASELINE_INITIAL_PHASE_FIT_INVALID")
                                    if not initial_phase.get("certified", False):
                                        reasons.append("BUNDLE_INITIAL_PHASE_NOT_CERTIFIED")
                                    if initial_delta_snr < dynamic.delta_omega_snr_min:
                                        reasons.append("LOW_INITIAL_DELTA_OMEGA_SNR")
                                    if not math.isfinite(q_signed):
                                        reasons.append("Q_NOT_FINITE")
                                    t_dyn_certified = not reasons
                                    run_pass = bool(t_dyn_certified and abs(q_signed - 1.0) <= dynamic.q_tolerance)

                                    resolved = bundle_summary["resolved_bundle"]
                                    area = math.pi * float(resolved["bundle_radius"]) ** 2
                                    gamma_over_area = float(resolved["total_circulation"]) / max(area, 1e-30)
                                    family_id = (
                                        f"zeta_{signed_zeta:+.8g}_r{resolution}_e{epsilon:.6g}_"
                                        f"{kernel}_{source.label}"
                                    )
                                    run_id = (
                                        f"{family_id}_{representation}_rr{radius_ratio:.6g}_"
                                        f"{row_counter:05d}"
                                    )
                                    row_counter += 1
                                    ts_file = None
                                    if dynamic.save_timeseries:
                                        ts_name = _safe_name(run_id) + ".npz"
                                        ts_path = timeseries_dir / ts_name
                                        np.savez_compressed(
                                            ts_path,
                                            **{f"bundle_{k}": v for k, v in bundle_arrays.items()},
                                            **{f"baseline_{k}": v for k, v in baseline_arrays.items()},
                                        )
                                        ts_file = str(ts_path.relative_to(output))

                                    row = {
                                        "run_id": run_id,
                                        "family_id": family_id,
                                        "label": source.label,
                                        "knot_id": source.knot_id,
                                        "mirror": source.mirror,
                                        "representation": representation,
                                        "base_protocol": asdict(base),
                                        "dynamic_clock_protocol": asdict(dynamic),
                                        "signed_mean_vorticity_target": signed_zeta,
                                        "gamma_over_area": gamma_over_area,
                                        "predicted_omega": predicted_omega,
                                        "predicted_period": predicted_period,
                                        "baseline_run": baseline_summary,
                                        "bundle_run": bundle_summary,
                                        "initial_background_omega_observed": initial_delta,
                                        "initial_background_omega_stderr": initial_se,
                                        "initial_delta_omega_snr": initial_delta_snr,
                                        "t_dyn": t_dyn,
                                        "q_gamma_signed": q_signed,
                                        "q_gamma_abs": q_abs,
                                        "q_gamma_stderr": q_stderr,
                                        "strict_background_omega_observed": strict_delta,
                                        "strict_t_dyn": strict_t_dyn,
                                        "strict_q_gamma_signed": strict_q,
                                        "baseline_fit_valid": baseline_fit_valid,
                                        "t_dyn_certified": t_dyn_certified,
                                        "t_dyn_certification_reason": "PASS" if not reasons else ";".join(reasons),
                                        "hypothesis_run_pass": run_pass,
                                        "timeseries_file": ts_file,
                                    }
                                    result["rows"].append(row)

    (output / "campaign_results.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    flat_rows = [_flatten_result(row) for row in result["rows"]]
    if flat_rows:
        with (output / "campaign_summary.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(flat_rows[0].keys()))
            writer.writeheader()
            writer.writerows(flat_rows)
    return result


def command_campaign(args: argparse.Namespace) -> int:
    result = run_campaign(_load_config(args.config), args.output)
    print(json.dumps({
        "status": "complete",
        "runs": len(result["rows"]),
        "output": str(Path(args.output).resolve()),
    }, indent=2))
    return 0


def command_selftest(_: argparse.Namespace) -> int:
    t = np.linspace(0.0, 10.0, 1001)
    omega = 2.3
    harmonic = 3
    m = 0.4 * np.exp(1j * harmonic * omega * t)
    protocol = DynamicClockProtocol(
        phase_harmonic=harmonic,
        target_predicted_cycles=3.0,
        burn_in_predicted_cycles=0.0,
        min_measured_cycles=2.0,
        phase_r2_min=0.999,
    )
    fit = extract_orientation_phase(t, m, protocol, TAU / abs(omega))
    scalar = np.sin(TAU * t / 1.25)
    shape = extract_scalar_period(t, scalar, protocol)
    checks = {
        "multipole_phase_rate": abs(float(fit["slope"]) - omega) < 1e-10,
        "multipole_certified": bool(fit["certified"]),
        "scalar_period": bool(shape["certified"]) and abs(float(shape["period"]) - 1.25) < 0.05,
    }
    print(json.dumps({"checks": checks, "phase_fit": fit, "shape_fit": shape}, indent=2))
    return 0 if all(checks.values()) else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="SST iso-Gamma/A dynamic-clock falsification harness")
    sub = p.add_subparsers(dest="command", required=True)
    pc = sub.add_parser("campaign")
    pc.add_argument("--config", required=True)
    pc.add_argument("--output", required=True)
    pc.set_defaults(func=command_campaign)
    ps = sub.add_parser("selftest")
    ps.set_defaults(func=command_selftest)
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
