"""SP10: knot datasets at new paths match SP00 freeze checksums."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import dataset_integrity as di  # noqa: E402

CHECKSUMS = WB / "10_docs" / "migration" / "checksums.sha256"
PATH_MAP = WB / "10_docs" / "migration" / "path_map.csv"


@pytest.mark.skipif(not CHECKSUMS.is_file(), reason="SP00 checksums missing")
def test_dataset_moves_are_listed():
    moves = di.dataset_moves(PATH_MAP)
    assert moves, "expected path_map rows into 03_data/A_knots/"
    assert any(new.endswith("04_knotplot") or "/04_knotplot" in new for _, new in moves)


@pytest.mark.skipif(not CHECKSUMS.is_file(), reason="SP00 checksums missing")
def test_dataset_integrity_sample_matches_freeze():
    # Cap per move so KnotPlot/knots does not hash multi-GB in CI.
    report = di.verify_datasets(max_files_per_move=50)
    assert report["checked"] > 0, report
    assert report["mismatched"] == [], report["mismatched"][:5]
    assert report["missing"] == [], report["missing"][:5]
    # Freeze drift (content changed after SP00 while move preserved bytes) is
    # allowed but must be visible.
    assert "freeze_drift" in report


def test_fremlin_move_preserves_bytes_even_if_freeze_drifted():
    digests = di.load_checksums()
    sample = "Fremlin_FourierSeries/fremlin/3_1/knot.3_1.fseries"
    if sample not in digests:
        pytest.skip("sample not in freeze checksums")
    new = WB / "03_data/A_knots/02_fourier/fremlin_fourier_series/fremlin/3_1/knot.3_1.fseries"
    old = WB / sample
    assert new.is_file() and old.is_file()
    assert di.sha256_file(new) == di.sha256_file(old)
