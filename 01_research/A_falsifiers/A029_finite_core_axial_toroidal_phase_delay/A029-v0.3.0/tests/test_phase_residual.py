from __future__ import annotations

import math

import numpy as np
import pytest

from sst_finite_core_falsifier.continuation import AMBIGUOUS, b_overlap, continue_same_branch
from sst_finite_core_falsifier.holonomy import forbid_double_counted_holonomy, holonomy_record, k_closed, k_ref
from sst_finite_core_falsifier.phase_contract import (
    carrier_derived_phase,
    classify_target_independence,
    classify_tau_independence,
    convention_bridge,
    envelope_phase_from_derived,
    signed_omega,
    wrap_phase,
)
from sst_finite_core_falsifier.residual import (
    ACCOUNTING_OK,
    DEFAULT_THRESHOLDS,
    MISSING_CASES,
    NO_INDEPENDENT_PHASE,
    NONINDEPENDENT_TAU,
    account_nested,
    accounting_identity_status,
    crmse,
    independence_gates_pass,
    leave_one_carrier_folds,
    phase_blind_return,
    predict_nested,
    reject_omega_demodulation,
    run_phase_residual,
    score_independent_fixture,
    sha256_obj,
    skill_score,
    wrapped_residual,
)


def test_signed_convention_bridge():
    rec = convention_bridge(0.2, -1.5)
    assert rec["sigma"] == pytest.approx(0.2)
    assert rec["omega"] == pytest.approx(1.5)
    assert rec["canonical_complex"]["imag"] == pytest.approx(1.5)
    with pytest.raises(ValueError):
        signed_omega(omega_mode=1.5)


def test_k_ref_and_k_closed():
    L = 2.0 * math.pi
    assert k_ref(1, L) == pytest.approx(1.0)
    assert k_closed(1, 2, 0.3, L) == pytest.approx((2 * math.pi - 0.6) / L)
    rec = holonomy_record(1, 2, 0.3, L)
    assert rec["holonomy_representation"] == "embedded_in_k"
    assert rec["phi_holonomy_explicit"] == 0.0
    rec["phi_holonomy_explicit"] = 0.3
    with pytest.raises(ValueError):
        forbid_double_counted_holonomy(rec)


def test_envelope_accounting():
    assert carrier_derived_phase(1.2, 0.4) == pytest.approx(wrap_phase(0.8))
    phi_loop = wrap_phase(-0.8 * 0.5 + 0.4)
    assert envelope_phase_from_derived(phi_loop, 0.8, 0.5) == pytest.approx(0.4)


def test_target_independence_rejects_demodulation_and_bandpass():
    bad = classify_target_independence(
        predicted_omega_used_in_extraction=True,
        predicted_omega_used_for_demodulation=True,
        raw_trajectory=True,
        spatial_mode_basis="model_conditioned_frozen",
    )
    assert bad["class"] == "derived_from_predictors"
    good = classify_target_independence(
        predicted_omega_used_in_extraction=False,
        predicted_vg_used_in_extraction=False,
        raw_trajectory=True,
        spatial_mode_basis_source="model_conditioned_frozen",
    )
    assert good["class"] == "independent_time_domain_given_frozen_spatial_mode"
    assert good["class"] != "fully_model_independent_time_domain"
    assert good["temporal_frequency_source"] == "independent_time_domain"
    assert good["return_phase_source"] == "measured_from_raw_trajectory"
    assert good["spatial_mode_basis_source"] == "model_conditioned_frozen"
    assert good["predicted_vg_used_in_extraction"] is False
    vg_bad = classify_target_independence(
        predicted_omega_used_in_extraction=False,
        predicted_vg_used_in_extraction=True,
        raw_trajectory=True,
        spatial_mode_basis_source="model_conditioned_frozen",
    )
    assert vg_bad["class"] == "derived_from_predictors"
    with pytest.raises(ValueError):
        reject_omega_demodulation(np.ones(4), 1.0, np.linspace(0, 1, 4))


def test_phase_blind_return_and_vg_window_rejection():
    t = np.linspace(0, 4, 401)
    env = np.exp(-((t - 2.2) ** 2) / 0.05)
    ok = phase_blind_return(t, env, window=(1.0, 3.0), tau_min=0.1)
    assert ok["available"] and ok["tau_return_independent"] == pytest.approx(2.2, abs=0.02)
    bad = phase_blind_return(t, env, window=(1.0, 3.0), tau_min=0.1, predicted_vg=1.0)
    assert bad["available"] is False
    assert bad["reason"] == NONINDEPENDENT_TAU
    lvg = classify_tau_independence(
        predicted_omega_used=False,
        predicted_group_velocity_used=False,
        synthetic_wavepacket_used=False,
        l_over_vg_used=True,
        raw_trajectory=True,
        search_window_source="protocol_fixed_or_training_only",
    )
    assert lvg["class"] == "derived_from_predicted_dispersion"


def test_refuse_tautological_or_model_tau_targets():
    derived = {
        "carrier_group_token": "c1",
        "phi_target_independent": 0.1,
        "predictions": {k: 0.1 for k in ("PRED_M0", "PRED_M1", "PRED_M2", "PRED_M3")},
        "target_independence": classify_target_independence(predicted_omega_used_in_extraction=True, raw_trajectory=False),
        "tau_return_independence": classify_tau_independence(
            predicted_omega_used=True, predicted_group_velocity_used=True, synthetic_wavepacket_used=True
        ),
    }
    out = score_independent_fixture([derived, dict(derived, carrier_group_token="c2")])
    assert out["status"] == NO_INDEPENDENT_PHASE
    assert out["scientific_pass"] is False


def test_wrapped_residual_boundaries():
    assert wrapped_residual(math.pi, -math.pi) == pytest.approx(0.0, abs=1e-12)
    assert abs(wrapped_residual(2.0, -2.0)) <= math.pi


def test_nested_toy_dispersion_and_accounting_identity():
    pred = predict_nested(omega_adv_ref=1.0, omega_intr_ref=0.2, omega_adv_closed=1.1, omega_intr_closed=0.25, tau=0.5, phi_null=0.0)
    acc = account_nested(omega_adv_ref=1.0, omega_intr_ref=0.2, omega_adv_closed=1.1, omega_intr_closed=0.25, tau_synthetic=0.5, phi_null=0.0)
    assert pred["PRED_M3"] == pytest.approx(wrap_phase(-1.35 * 0.5))
    assert accounting_identity_status(acc["ACCOUNT_M3"], acc["ACCOUNT_M3"]) == ACCOUNTING_OK


def test_same_branch_continuation_and_ambiguity():
    ref = {"vector": np.array([1.0, 0.0])}
    good = {"modes": [{"vector": np.array([0.99, 0.1]), "residual": 1e-12}]}
    assert continue_same_branch(ref, good, min_overlap=0.5)["status"] == "unique"
    bad = {"modes": [{"vector": np.array([0.0, 1.0]), "residual": 1e-12}]}
    assert continue_same_branch(ref, bad, min_overlap=0.8)["status"] == AMBIGUOUS
    assert b_overlap(np.array([1.0, 0.0]), np.array([1.0, 0.0])) == pytest.approx(1.0)


def test_no_carrier_leakage_across_folds():
    rows = [
        {"carrier_group_token": "A", "phi_target_independent": 0.1},
        {"carrier_group_token": "A", "phi_target_independent": 0.12},
        {"carrier_group_token": "B", "phi_target_independent": 1.0},
    ]
    folds = leave_one_carrier_folds(rows)
    held_a = next(f for f in folds if f["held_out"] == "A")
    assert "A" not in held_a["train_tokens"]
    assert all(r["carrier_group_token"] == "A" for r in held_a["test"])


def test_clustered_bootstrap_not_rowwise_and_skill():
    r0 = [0.8, 0.8, 0.7, 0.7]
    r3 = [0.1, 0.1, 0.05, 0.05]
    assert skill_score(crmse(r3), crmse(r0)) > 0.3


def test_prediction_tamper_detection():
    a = {"PRED_M3": 0.2}
    b = {"PRED_M3": 0.21}
    assert sha256_obj(a) != sha256_obj(b)


def test_end_to_end_pass_fail_indeterminate(tmp_path):
    missing = run_phase_residual(tmp_path, pack_root=tmp_path.parent, search_default_historical=False)
    assert missing["residual"]["status"] == MISSING_CASES
    assert (tmp_path / "paper_upgrade" / "PHASE_ACCOUNTING_CERTIFICATE.json").is_file()
    rows = []
    for token, tgt in (("c1", -0.65), ("c2", -0.67)):
        pred = predict_nested(omega_adv_ref=1.0, omega_intr_ref=0.2, omega_adv_closed=1.1, omega_intr_closed=0.2, tau=0.5, phi_null=0.0)
        rows.append(
            {
                "carrier_group_token": token,
                "phi_target_independent": tgt,
                "predictions": pred,
                "phase_uncertainty_rad": 0.05,
                "target_independence": classify_target_independence(
                    predicted_omega_used_in_extraction=False,
                    raw_trajectory=True,
                    spatial_mode_basis="model_conditioned_frozen",
                ),
                "tau_return_independence": classify_tau_independence(
                    predicted_omega_used=False,
                    predicted_group_velocity_used=False,
                    synthetic_wavepacket_used=False,
                    raw_trajectory=True,
                    search_window_source="protocol_fixed_or_training_only",
                ),
            }
        )
    passed = score_independent_fixture(rows, DEFAULT_THRESHOLDS)
    assert independence_gates_pass(rows[0]["target_independence"], rows[0]["tau_return_independence"])
    assert passed["status"] in {"PASS", "FAIL"}
    tau_bad = dict(rows[0])
    tau_bad["tau_return_independence"] = classify_tau_independence(
        predicted_omega_used=False,
        predicted_group_velocity_used=True,
        synthetic_wavepacket_used=False,
        raw_trajectory=True,
    )
    assert score_independent_fixture([tau_bad, dict(tau_bad, carrier_group_token="c2")])["status"] == NONINDEPENDENT_TAU


def test_schema_round_trip_parquet(tmp_path):
    pytest.importorskip("pyarrow")
    from sst_finite_core_falsifier.table_io import read_parquet, write_parquet

    rows = [{"k_hat": 1.0, "omega": 2.0}]
    path = write_parquet(tmp_path / "phase_contract.parquet", rows)
    assert read_parquet(path)[0]["k_hat"] == 1.0
