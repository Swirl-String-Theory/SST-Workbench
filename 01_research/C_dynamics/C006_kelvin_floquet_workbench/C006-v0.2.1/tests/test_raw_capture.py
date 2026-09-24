import numpy as np
import pytest
from sst_kelvin_workbench.raw_capture import write_raw_modal_timeseries


def test_scientific_requires_qualified(tmp_path):
    with pytest.raises(ValueError, match="BRIDGE_QUALIFIED"):
        write_raw_modal_timeseries(
            tmp_path / "x.json",
            t=[0.0, 1.0],
            a=[1.0, 1.0],
            source_id="C006",
            spatial_basis=np.array([1.0, 0.0]),
            scientific=True,
            extra={"bridge_status": "BRIDGE_REJECTED", "mode_recon_status": "RECONSTRUCTED_SAME_BRANCH", "tube_status": "TUBE_VALID"},
        )


def test_writer_marks_unscored(tmp_path):
    rec = write_raw_modal_timeseries(
        tmp_path / "x.json",
        t=[0.0, 1.0],
        a=[1.0 + 0j, 0.5 + 0.2j],
        source_id="C006",
        spatial_basis=np.array([1.0 + 1j, 0.0]),
        scientific=True,
        extra={
            "bridge_status": "BRIDGE_QUALIFIED",
            "mode_recon_status": "RECONSTRUCTED_SAME_BRANCH",
            "tube_status": "TUBE_VALID",
            "prediction_inputs_consumed": [],
            "d_set": "D_bridge",
        },
    )
    assert rec["scored"] is False
    assert rec["prediction_inputs_consumed"] == []
    assert rec["provider_id"] == "C006"
