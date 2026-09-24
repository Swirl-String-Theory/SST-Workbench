from pathlib import Path

from pklsa_builder.repo_finder import _classify_catalog_file
from pklsa_builder.source_discovery import _infer_a007_family, _representation_from_record


def test_a007_fremlin_short_mirror_is_xyz(tmp_path):
    root = tmp_path / "06_knot_library"
    p = root / "Sources" / "FourierSeries_Fremlin" / "extracted" / "3_1" / "knot.3_1.short"
    p.parent.mkdir(parents=True)
    p.write_text(
        "-1.095785 -0.008559 0.619099\n"
        "-1.000000  0.100000 0.600000\n"
        "-0.900000  0.200000 0.580000\n",
        encoding="utf-8",
    )

    role, hint = _classify_catalog_file(p, "A007", root)
    assert role == "source_geometry"
    assert hint == "xyz_short"

    family, *_rest = _infer_a007_family(p, role)
    rec = {"path": str(p), "representation_hint": hint}
    assert family == "fremlin_fourier_mirror"
    assert _representation_from_record(rec, family) == "xyz"


def test_a007_fremlin_fseries_mirror_stays_fseries(tmp_path):
    root = tmp_path / "06_knot_library"
    p = root / "Sources" / "FourierSeries_Fremlin" / "extracted" / "3_1" / "knot.3_1.fseries"
    p.parent.mkdir(parents=True)
    p.write_text("1 2 3 4 5 6\n", encoding="utf-8")

    role, hint = _classify_catalog_file(p, "A007", root)
    assert role == "source_geometry"
    assert hint == "fseries"

    family, *_rest = _infer_a007_family(p, role)
    rec = {"path": str(p), "representation_hint": hint}
    assert family == "fremlin_fourier_mirror"
    assert _representation_from_record(rec, family) == "fremlin_fseries"
