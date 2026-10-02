"""SP09 tests for short-name mapping and FAMILY.yaml rewrite."""
from __future__ import annotations

import sys
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import catalog_metadata as cm  # noqa: E402
import version_rename as vr  # noqa: E402


def test_rewrite_replaces_quoted_directory_fields():
    text = '  - id: v0.1.0\n    directory: "SST_Pack_v0.1.0"\n'
    out = vr.rewrite_family_yaml_directories(text, {"SST_Pack_v0.1.0": "A042-v0.1.0"})
    assert 'directory: "A042-v0.1.0"' in out
    assert "SST_Pack_v0.1.0" not in out


def test_a042_mapping_is_the_sp09_table():
    fam = next(f for f in cm.discover() if f.catalog_id == "A042" and f.domain == "01_research")
    mapping = cm.short_names_for_family(fam)
    assert set(mapping.values()) == {"A042-v0.1.0", "A042-v0.2.0"}


def test_a023_config_versions_stay_unique_without_sharing_a_name():
    fam = next(f for f in cm.discover() if f.catalog_id == "A023" and f.domain == "01_research")
    mapping = cm.short_names_for_family(fam)
    shorts = list(mapping.values())
    assert len(shorts) == len(set(shorts))
    assert "A023-v0.4.5-r3" in shorts
    assert "A023-v0.4.8" in shorts


def test_c005_keeps_plain_v043_when_flat_variant_exists():
    fam = next(f for f in cm.discover() if f.catalog_id == "C005" and f.domain == "01_research")
    mapping = cm.short_names_for_family(fam)
    shorts = set(mapping.values())
    assert "C005-v0.4.3" in shorts
    assert "C005-v0.4.3-flat" in shorts
    assert mapping["C005-v0.4.3"] == "C005-v0.4.3"


def test_family_legacy_root_is_a_single_component():
    fam = next(f for f in cm.discover() if f.catalog_id == "A042" and f.domain == "01_research")
    assert vr.family_legacy_root(fam) == "SST_Quantum_Galileo_Action_Gauge_Closure"


def test_should_retarget_root_when_legacy_name_is_the_root():
    dest = Path("01_research/A_falsifiers/A020_six_source_blind_energy/A020-v0.1.0")
    assert vr.should_retarget_root(
        "SST_6Source_Blind_Falsifier_v0.1.0",
        [("SST_6Source_Blind_Falsifier_v0.1.0", dest)],
    )
    assert not vr.should_retarget_root(
        "SST_ideal_links",
        [("SST_ideal_links_comprehensive_test_suite_v0.1.0", dest)],
    )


def test_absorb_leftover_moves_untracked_children_then_removes_husk(tmp_path: Path):
    src = tmp_path / "old_dir"
    dest = tmp_path / "A007-v0.2.1"
    (src / ".venv" / "lib").mkdir(parents=True)
    (src / ".venv" / "lib" / "marker.txt").write_text("venv", encoding="utf-8")
    (src / "src").mkdir()
    (dest / "src").mkdir(parents=True)
    (dest / "project.json").write_text("{}", encoding="utf-8")
    (dest / "src" / "kept.py").write_text("ok", encoding="utf-8")

    vr.absorb_leftover(src, dest)

    assert not src.exists()
    assert (dest / "project.json").is_file()
    assert (dest / "src" / "kept.py").read_text(encoding="utf-8") == "ok"
    assert (dest / ".venv" / "lib" / "marker.txt").read_text(encoding="utf-8") == "venv"


def test_yaml_rewrite_map_includes_legacy_dir(tmp_path: Path):
    fam_dir = tmp_path / "A007_ideal_links"
    dest = fam_dir / "A007-v0.2.1"
    dest.mkdir(parents=True)
    (dest / "project.json").write_text(
        '{"version": "v0.2.1", "legacy_dir": '
        '"SST_ideal_links_comprehensive_test_suite_v0.2.1"}',
        encoding="utf-8",
    )
    fam = cm.Family(
        catalog_id="A007", slug="ideal_links", domain="01_research",
        letter="A_falsifiers", path=fam_dir,
        versions=[cm.Version(directory="A007-v0.2.1", version="v0.2.1")],
    )
    mapping = {"A007-v0.2.1": "A007-v0.2.1"}
    out = vr.yaml_rewrite_map(fam, mapping)
    assert out["A007-v0.2.1"] == "A007-v0.2.1"
    assert out["SST_ideal_links_comprehensive_test_suite_v0.2.1"] == "A007-v0.2.1"
