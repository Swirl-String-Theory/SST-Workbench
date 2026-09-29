from __future__ import annotations

import numpy as np
import pytest

from sst_finite_core_falsifier.observable import (
    PHYSICAL_ROLES,
    detect_independent_return,
    extra_residual_gates,
    extract_observed_phase,
    frozen_search_window,
    increment_skills,
    label_frozen_spatial_target,
    phase_at_time,
    refuse_predicted_demodulation,
    window_uses_predictor,
)


def test_physical_roles_keep_m0_as_null():
    assert PHYSICAL_ROLES["PRED_M0"] == "null_leave_one_carrier_circular_mean"
    assert PHYSICAL_ROLES["PRED_M1"] == "advection_at_k_ref"
    assert PHYSICAL_ROLES["PRED_M3"] == "closed_loop_via_k_closed"


def test_extract_observed_phase_without_omega():
    a0 = 1 + 0j
    a1 = np.exp(1j * 0.4)
    assert extract_observed_phase(a0, a1) == pytest.approx(0.4)


def test_frozen_window_rejects_predictor_and_l_over_vg():
    assert window_uses_predictor(predicted_omega=1.0, predicted_vg=None, l_over_vg=None)
    assert window_uses_predictor(predicted_omega=None, predicted_vg=None, l_over_vg=12.0)
    assert not window_uses_predictor(predicted_omega=None, predicted_vg=None, l_over_vg=None)
    assert frozen_search_window(1.0, 3.0) == (1.0, 3.0)
    with pytest.raises(ValueError):
        frozen_search_window(3.0, 1.0)


def test_detect_independent_return_and_phase_at_time():
    t = np.linspace(0.0, 4.0, 401)
    a = np.exp(-((t - 2.2) ** 2) / 0.05) * np.exp(1j * 0.15 * t)
    det = detect_independent_return(t, np.abs(a), window=(1.0, 3.0), tau_min=0.1)
    assert det["available"]
    assert det["tau_return_independent"] == pytest.approx(2.2, abs=0.02)
    assert phase_at_time(t, a, det["tau_return_independent"]) == pytest.approx(0.33, abs=0.05)


def test_increments_and_advection_gate():
    skills = {"PRED_M0": 0.0, "PRED_M1": 0.8, "PRED_M2": 0.81, "PRED_M3": 0.82}
    inc = increment_skills(skills)
    assert inc["delta_S_10"] == pytest.approx(0.8)
    assert extra_residual_gates(skills)["m3_beats_advection"] is True
    adv_dom = {"PRED_M0": 0.0, "PRED_M1": 0.9, "PRED_M2": 0.85, "PRED_M3": 0.84}
    assert extra_residual_gates(adv_dom)["extra_gate_pass"] is False


def test_frozen_spatial_target_is_not_fully_independent():
    rec = label_frozen_spatial_target()
    assert rec["class"] == "independent_time_domain_given_frozen_spatial_mode"
    assert rec["class"] != "fully_model_independent_time_domain"


def test_refuse_demodulation():
    with pytest.raises(ValueError):
        refuse_predicted_demodulation(np.ones(4), 1.0, np.linspace(0, 1, 4))
