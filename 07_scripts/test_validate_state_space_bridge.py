from __future__ import annotations

import pytest

from validate_state_space_bridge import (
    BRIDGE,
    RECON,
    TUBE,
    BridgeCertError,
    validate_bridge_certificate,
)


def _bridge(**extra):
    rec = {
        "schema": BRIDGE,
        "schema_version": "1.0",
        "record_type": "state_space_bridge",
        "status": "BRIDGE_QUALIFIED",
        "prediction_inputs_consumed": [],
        "scientific_amplitude": "left_eigenvector_Wr_B",
        "d_bridge": ["ring", "c1630473578eb8fa"],
        "d_score": [],
        "holdout_scoring_enabled": False,
        "bridge_rejected_falsifies_a029_clock": False,
    }
    rec.update(extra)
    return rec


def _recon(**extra):
    rec = {
        "schema": RECON,
        "schema_version": "1.0",
        "record_type": "mode_reconstruction",
        "status": "RECONSTRUCTED_SAME_BRANCH",
        "carrier_id": "c1630473578eb8fa",
        "q_hash": "a" * 64,
        "p_hash": "b" * 64,
        "biorthogonality_residual": 1e-12,
    }
    rec.update(extra)
    return rec


def _tube(**extra):
    rec = {
        "schema": TUBE,
        "schema_version": "1.0",
        "record_type": "tube_validity",
        "status": "TUBE_VALID",
        "rmax": 5.0,
        "rmax_was_reduced": False,
        "c_kappa": 0.30,
        "c_d": 1.0,
    }
    rec.update(extra)
    return rec


def test_bridge_ok():
    assert validate_bridge_certificate(_bridge())["ok"] is True


def test_bridge_rejects_prediction_inputs():
    with pytest.raises(BridgeCertError, match="prediction_inputs_consumed"):
        validate_bridge_certificate(_bridge(prediction_inputs_consumed=["omega_pred"]))


def test_bridge_rejects_right_vector_amplitude():
    with pytest.raises(BridgeCertError, match="left_eigenvector"):
        validate_bridge_certificate(_bridge(scientific_amplitude="q_dagger_B"))


def test_bridge_rejects_overlapping_sets():
    with pytest.raises(BridgeCertError, match="disjoint"):
        validate_bridge_certificate(_bridge(d_score=["ring"]))


def test_bridge_rejects_clock_falsified_claim():
    with pytest.raises(BridgeCertError, match="must not falsify"):
        validate_bridge_certificate(_bridge(bridge_rejected_falsifies_a029_clock=True))


def test_recon_ok():
    assert validate_bridge_certificate(_recon())["status"] == "RECONSTRUCTED_SAME_BRANCH"


def test_recon_rejects_short_hash():
    with pytest.raises(BridgeCertError, match="q_hash"):
        validate_bridge_certificate(_recon(q_hash="abc"))


def test_tube_ok():
    assert validate_bridge_certificate(_tube())["ok"] is True


def test_tube_rejects_rmax_reduction():
    with pytest.raises(BridgeCertError, match="r_max"):
        validate_bridge_certificate(_tube(rmax_was_reduced=True))
