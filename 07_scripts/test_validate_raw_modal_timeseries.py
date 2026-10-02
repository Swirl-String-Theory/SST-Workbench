from __future__ import annotations

import pytest

from validate_raw_modal_timeseries import (
    SCHEMA_NAME,
    TimeseriesError,
    load_schema,
    spatial_basis_hash,
    validate_raw_timeseries,
)


def _series(**extra):
    rec = {
        "schema": SCHEMA_NAME,
        "schema_version": "1.0",
        "record_type": "raw_modal_timeseries",
        "source_id": "A029-v0.4.0",
        "t": [0.0, 1.0, 2.0],
        "a_real": [1.0, 0.7, 0.2],
        "a_imag": [0.0, 0.2, 0.1],
        "spatial_mode_basis_source": "model_conditioned_frozen",
        "spatial_basis_hash": spatial_basis_hash([1.0, 0.0]),
        "written_before_predictor_postprocess": True,
        "predicted_omega_used_in_extraction": False,
        "predicted_vg_used_in_extraction": False,
        "predicted_omega_used_for_demodulation": False,
        "predicted_omega_used_for_bandpass": False,
        "synthetic_wavepacket_used": False,
        "scientific": False,
        "selftest": True,
    }
    rec.update(extra)
    return rec


def test_load_schema_title():
    assert load_schema()["title"] == SCHEMA_NAME


def test_validate_selftest_ok():
    assert validate_raw_timeseries(_series())["ok"] is True


def test_validate_rejects_length_mismatch():
    with pytest.raises(TimeseriesError, match="same length"):
        validate_raw_timeseries(_series(a_real=[1.0]))


def test_validate_rejects_scientific_selftest():
    with pytest.raises(TimeseriesError, match="SELFTEST"):
        validate_raw_timeseries(_series(scientific=True, selftest=True))


def test_validate_rejects_scientific_demodulation():
    with pytest.raises(TimeseriesError, match="predictor"):
        validate_raw_timeseries(
            _series(scientific=True, selftest=False, predicted_omega_used_for_demodulation=True)
        )


def test_validate_rejects_frozen_basis_as_fully_independent():
    with pytest.raises(TimeseriesError, match="not fully model-independent"):
        validate_raw_timeseries(_series(fully_model_independent=True))
