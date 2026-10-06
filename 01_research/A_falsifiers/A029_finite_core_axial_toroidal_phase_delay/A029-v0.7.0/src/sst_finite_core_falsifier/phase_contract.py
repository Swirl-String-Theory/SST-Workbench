"""Sign-safe phase/eigenvalue contract helpers for A029-v0.4.0."""

from __future__ import annotations

import math
from typing import Any

from .delay import wrap

RAW_CONVENTION = "lambda_raw = sigma - i*omega"
CANONICAL_CONVENTION = "mu = sigma + i*omega"


def wrap_phase(phi: float) -> float:
    return wrap(phi)


def convention_bridge(lambda_real: float, lambda_imag: float, *, omega: float | None = None) -> dict[str, Any]:
    sigma = float(lambda_real)
    omega_from_imag = -float(lambda_imag)
    omega_used = omega_from_imag if omega is None else float(omega)
    if abs(omega_used - omega_from_imag) > 1e-12 * (1.0 + abs(omega_from_imag)):
        raise ValueError("omega must equal -Im(lambda_raw)")
    return {
        "eigenvalue_raw": {"real": sigma, "imag": float(lambda_imag), "convention": RAW_CONVENTION},
        "sigma": sigma,
        "omega": omega_used,
        "canonical_complex": {"real": sigma, "imag": omega_used, "convention": CANONICAL_CONVENTION},
    }


def signed_omega(*, omega_median: float | None = None, lambda_imag: float | None = None, omega_mode: float | None = None) -> float:
    if omega_mode is not None and omega_median is None and lambda_imag is None:
        raise ValueError("omega_mode is absolute-valued and must not be used for phase prediction")
    if omega_median is not None:
        return float(omega_median)
    if lambda_imag is not None:
        return -float(lambda_imag)
    raise ValueError("signed omega requires omega_median or -lambda_imag")


def carrier_derived_phase(phi_loop: float, phi_envelope: float) -> float:
    return wrap_phase(float(phi_loop) - float(phi_envelope))


def envelope_phase_from_derived(phi_loop: float, omega: float, tau: float) -> float:
    """Invert phi_loop = wrap(-omega * tau + arg(envelope))."""
    return wrap_phase(float(phi_loop) + float(omega) * float(tau))


def classify_target_independence(
    *,
    predicted_omega_used_in_extraction: bool,
    predicted_omega_used_for_demodulation: bool = False,
    predicted_omega_used_for_bandpass: bool = False,
    predicted_vg_used_in_extraction: bool = False,
    spatial_mode_basis_source: str | None = None,
    spatial_mode_basis: str | None = None,
    raw_trajectory: bool = False,
    temporal_frequency_source: str | None = None,
    return_phase_source: str | None = None,
) -> dict[str, Any]:
    basis = spatial_mode_basis_source or spatial_mode_basis or "unavailable"
    used_omega = bool(predicted_omega_used_in_extraction or predicted_omega_used_for_demodulation or predicted_omega_used_for_bandpass)
    used_vg = bool(predicted_vg_used_in_extraction)
    if used_omega or used_vg or not raw_trajectory:
        klass = "derived_from_predictors"
    elif basis == "model_conditioned_frozen":
        klass = "independent_time_domain_given_frozen_spatial_mode"
    elif basis == "measurement_fixed":
        klass = "fully_model_independent_time_domain"
    else:
        klass = "unavailable"
    if klass == "fully_model_independent_time_domain" and basis != "measurement_fixed":
        raise ValueError("fully_model_independent_time_domain requires a measurement-fixed spatial basis")
    if klass == "fully_model_independent_time_domain" and basis == "model_conditioned_frozen":
        raise ValueError("a frozen modal spatial basis is not fully model-independent")
    freq_source = temporal_frequency_source or ("independent_time_domain" if not used_omega and not used_vg and raw_trajectory else "derived_from_predictors")
    phase_source = return_phase_source or ("measured_from_raw_trajectory" if raw_trajectory and not used_omega and not used_vg else "derived_from_predictors")
    return {
        "class": klass,
        "temporal_frequency_source": freq_source,
        "return_phase_source": phase_source,
        "spatial_mode_basis_source": basis,
        "predicted_omega_used_in_extraction": bool(predicted_omega_used_in_extraction),
        "predicted_vg_used_in_extraction": bool(used_vg),
        "temporal_frequency": "independent" if freq_source.startswith("independent") else "derived",
        "return_phase": phase_source,
        "spatial_mode_basis": basis,
        "predicted_omega_used_for_demodulation": bool(predicted_omega_used_for_demodulation),
        "predicted_omega_used_for_bandpass": bool(predicted_omega_used_for_bandpass),
        "predicted_vg_used": bool(used_vg),
    }


def classify_tau_independence(
    *,
    predicted_omega_used: bool,
    predicted_group_velocity_used: bool,
    synthetic_wavepacket_used: bool,
    l_over_vg_used: bool = False,
    raw_trajectory: bool = False,
    search_window_source: str = "unavailable",
) -> dict[str, Any]:
    used = bool(predicted_omega_used or predicted_group_velocity_used or synthetic_wavepacket_used or l_over_vg_used)
    if used:
        klass = "derived_from_predicted_dispersion"
    elif raw_trajectory and search_window_source in {"protocol_fixed_or_training_only", "protocol_fixed"}:
        klass = "raw_trajectory_phase_blind"
    elif raw_trajectory:
        klass = "model_conditioned"
    else:
        klass = "unavailable"
    return {
        "class": klass,
        "search_window_source": search_window_source,
        "predicted_omega_used": bool(predicted_omega_used),
        "predicted_group_velocity_used": bool(predicted_group_velocity_used),
        "synthetic_wavepacket_used": bool(synthetic_wavepacket_used),
        "l_over_vg_used": bool(l_over_vg_used),
        "l_over_vg_sensitivity_only": True,
    }


def identity_fields(source_id: str, parent_hashes: dict[str, Any], code_hash: str, *, record_type: str, blind_status: str = "retrospective_prediction_locked") -> dict[str, Any]:
    return {
        "schema": "SST_MODAL_PHASE_CONTRACT-1.0",
        "schema_version": "1.0",
        "record_type": record_type,
        "source_id": source_id,
        "parent_hashes": parent_hashes,
        "code_hash": code_hash,
        "blind_status": blind_status,
    }
