from __future__ import annotations

import numpy as np
import pytest

from sst_finite_core_falsifier.raw_timeseries import (
    find_raw_modal_timeseries,
    load_scientific_series,
    series_is_contaminated,
    series_is_scientific,
    spatial_basis_hash,
    write_raw_modal_timeseries,
)


def test_spatial_basis_hash_stable():
    assert spatial_basis_hash([1.0, 0.0]) == spatial_basis_hash(np.array([1.0, 0.0]))
    assert spatial_basis_hash([1.0, 0.0]) != spatial_basis_hash([0.0, 1.0])


def test_write_and_discover_selftest_is_not_scientific(tmp_path):
    t = np.linspace(0.0, 1.0, 8)
    a = np.exp(-1j * 2.0 * t)
    path = tmp_path / "raw_timeseries" / "demo_raw_am.json"
    rec = write_raw_modal_timeseries(
        path,
        t=t,
        a=a,
        source_id="selftest",
        spatial_basis=[1.0, 0.0],
        scientific=False,
        selftest=True,
    )
    assert rec["schema"] == "SST_RAW_MODAL_TIMESERIES-1.0"
    assert series_is_scientific(rec) is False
    found = find_raw_modal_timeseries(tmp_path)
    assert found == [path.resolve()]
    assert load_scientific_series(found) == []


def test_refuse_scientific_selftest(tmp_path):
    with pytest.raises(ValueError, match="SELFTEST"):
        write_raw_modal_timeseries(
            tmp_path / "x.json",
            t=[0.0, 1.0],
            a=[1 + 0j, 1 + 0j],
            source_id="bad",
            spatial_basis=[1.0],
            scientific=True,
            selftest=True,
        )


def test_contaminated_series_is_not_scientific():
    rec = {
        "written_before_predictor_postprocess": True,
        "predicted_omega_used_in_extraction": True,
        "predicted_vg_used_in_extraction": False,
        "predicted_omega_used_for_demodulation": False,
        "predicted_omega_used_for_bandpass": False,
        "synthetic_wavepacket_used": False,
        "scientific": True,
        "selftest": False,
    }
    assert series_is_contaminated(rec)
    assert series_is_scientific(rec) is False
