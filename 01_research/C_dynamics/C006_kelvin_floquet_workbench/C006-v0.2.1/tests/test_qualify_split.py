import sys

import pytest

from sst_kelvin_workbench.paths import workbench_root
from sst_kelvin_workbench.qualify import forbid_a029_scoring

SCRIPTS = workbench_root() / "07_scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from validate_state_space_bridge import BridgeCertError, validate_bridge_certificate


def test_forbid_a029_scoring():
    with pytest.raises(RuntimeError, match="must not feed A029"):
        forbid_a029_scoring()


def test_bridge_cert_keeps_score_set_empty():
    rec = {
        "schema": "SST_STATE_SPACE_BRIDGE-1.0",
        "schema_version": "1.0",
        "record_type": "state_space_bridge",
        "status": "INDETERMINATE_TUBE_CHART_INVALID",
        "prediction_inputs_consumed": [],
        "scientific_amplitude": "left_eigenvector_Wr_B",
        "d_bridge": ["ring", "c1630473578eb8fa"],
        "d_score": [],
        "holdout_scoring_enabled": False,
        "bridge_rejected_falsifies_a029_clock": False,
    }
    assert validate_bridge_certificate(rec)["ok"] is True


def test_overlapping_sets_are_illegal():
    rec = {
        "schema": "SST_STATE_SPACE_BRIDGE-1.0",
        "schema_version": "1.0",
        "record_type": "state_space_bridge",
        "status": "BRIDGE_QUALIFIED",
        "prediction_inputs_consumed": [],
        "scientific_amplitude": "left_eigenvector_Wr_B",
        "d_bridge": ["ring"],
        "d_score": ["ring"],
        "holdout_scoring_enabled": False,
        "bridge_rejected_falsifies_a029_clock": False,
    }
    with pytest.raises(BridgeCertError, match="disjoint"):
        validate_bridge_certificate(rec)
