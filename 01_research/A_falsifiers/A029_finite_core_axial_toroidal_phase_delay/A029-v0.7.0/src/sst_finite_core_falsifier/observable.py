"""Independent phase extraction and nested-skill increments for A029-v0.4.0."""

from __future__ import annotations

from typing import Any

import numpy as np

from .phase_contract import classify_target_independence, classify_tau_independence, wrap_phase
from .residual import independent_return_phase, phase_blind_return, reject_omega_demodulation

PHYSICAL_ROLES = {
    "PRED_M0": "null_leave_one_carrier_circular_mean",
    "PRED_M1": "advection_at_k_ref",
    "PRED_M2": "advection_plus_intrinsic_at_k_ref",
    "PRED_M3": "closed_loop_via_k_closed",
}


def extract_observed_phase(a0: complex, a_return: complex) -> float:
    return independent_return_phase(a0, a_return)


def refuse_predicted_demodulation(signal: np.ndarray, omega: float, t: np.ndarray) -> None:
    reject_omega_demodulation(signal, omega, t)


def window_uses_predictor(*, predicted_omega: float | None, predicted_vg: float | None, l_over_vg: float | None) -> bool:
    return predicted_omega is not None or predicted_vg is not None or l_over_vg is not None


def frozen_search_window(t_min: float, t_max: float) -> tuple[float, float]:
    if not (t_max > t_min):
        raise ValueError("frozen search window must have t_max > t_min")
    return (float(t_min), float(t_max))


def detect_independent_return(t, envelope, *, window: tuple[float, float], tau_min: float) -> dict[str, Any]:
    return phase_blind_return(np.asarray(t, dtype=float), np.asarray(envelope, dtype=float), window=window, tau_min=tau_min)


def increment_skills(skills: dict[str, float]) -> dict[str, float]:
    return {
        "delta_S_10": float(skills["PRED_M1"]) - float(skills["PRED_M0"]),
        "delta_S_21": float(skills["PRED_M2"]) - float(skills["PRED_M1"]),
        "delta_S_32": float(skills["PRED_M3"]) - float(skills["PRED_M2"]),
    }


def extra_residual_gates(skills: dict[str, float], *, require_beats_advection: bool = True) -> dict[str, bool]:
    beats_null = float(skills["PRED_M3"]) > float(skills["PRED_M0"])
    beats_adv = float(skills["PRED_M3"]) > float(skills["PRED_M1"])
    return {
        "m3_beats_null": beats_null,
        "m3_beats_advection": beats_adv,
        "extra_gate_pass": bool(beats_null and (beats_adv if require_beats_advection else True)),
    }


def label_frozen_spatial_target() -> dict[str, Any]:
    rec = classify_target_independence(
        predicted_omega_used_in_extraction=False,
        predicted_vg_used_in_extraction=False,
        raw_trajectory=True,
        spatial_mode_basis_source="model_conditioned_frozen",
    )
    if rec["class"] == "fully_model_independent_time_domain":
        raise ValueError("a frozen modal spatial basis is not fully model-independent")
    return rec


def label_phase_blind_tau() -> dict[str, Any]:
    return classify_tau_independence(
        predicted_omega_used=False,
        predicted_group_velocity_used=False,
        synthetic_wavepacket_used=False,
        l_over_vg_used=False,
        raw_trajectory=True,
        search_window_source="protocol_fixed_or_training_only",
    )


def complex_envelope(a) -> np.ndarray:
    return np.abs(np.asarray(a, dtype=complex))


def phase_at_time(t, a, tau: float) -> float:
    t = np.asarray(t, dtype=float)
    a = np.asarray(a, dtype=complex)
    idx = int(np.argmin(np.abs(t - float(tau))))
    return extract_observed_phase(a[0], a[idx])


def wrap_residual(target: float, pred: float) -> float:
    return wrap_phase(float(target) - float(pred))
