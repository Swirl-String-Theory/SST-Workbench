"""Tests for build_family_hierarchy.py."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).with_name("build_family_hierarchy.py")
WB = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("build_family_hierarchy", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_expected_outputs_zip_naming():
    m = _load()
    assert (
        m.expected_outputs_zip("1_Maxwell_SST_Kinetic_Falsifier", "v0.3.1")
        == "1_Maxwell_SST_Kinetic_Falsifier_v0.3.1_outputs.zip"
    )
    assert m.expected_outputs_zip("", "v0.1.0") is None


def test_scan_family_disk_finds_outputs(tmp_path: Path):
    m = _load()
    fam = tmp_path / "A011_maxwell_1_kinetic_energy"
    ver = fam / "A011-v0.3.1"
    ver.mkdir(parents=True)
    zip_name = "1_Maxwell_SST_Kinetic_Falsifier_v0.3.1_outputs.zip"
    (ver / zip_name).write_bytes(b"x")
    (ver / f"{zip_name}.sha256").write_text("deadbeef", encoding="utf-8")
    (ver / "project.json").write_text("{}", encoding="utf-8")
    (fam / "notes").mkdir()

    meta = {
        "output_prefix": "1_Maxwell_SST_Kinetic_Falsifier",
        "versions": [{"id": "v0.3.1", "directory": "A011-v0.3.1"}],
    }
    disk = m.scan_family_disk(fam, meta)
    node = disk["versions_on_disk"]["v0.3.1"]
    assert node["expected_zip_present"] is True
    assert zip_name in node["outputs_zips"]
    assert node["has_project_json"] is True
    assert "notes" in disk["other_dirs"]


def test_next_catalog_ids():
    m = _load()
    got = m.next_catalog_ids(
        {
            "A_falsifiers": {"A011": {}, "A032": {}},
            "B_closures": {"B001": {}},
        }
    )
    assert got["A_falsifiers"] == "A033"
    assert got["B_closures"] == "B002"


def test_live_hierarchy_includes_a011_outputs():
    m = _load()
    payload = m.build(WB)
    a011 = payload["hierarchy"]["01_research"]["A_falsifiers"]["A011"]
    assert a011["output_prefix"] == "1_Maxwell_SST_Kinetic_Falsifier"
    assert "v0.3.1" in a011["versions_on_disk"]
    all_zips = [
        z
        for v in a011["versions_on_disk"].values()
        for z in v.get("outputs_zips") or []
    ]
    assert any("Maxwell_SST_Kinetic" in z for z in all_zips)
    assert "A011" in payload["by_catalog_id"]
    assert "naming" in payload
