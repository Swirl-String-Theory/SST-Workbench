"""Unit tests for consolidate_archives classification and collision handling."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).with_name("consolidate_archives.py")


def _load():
    spec = importlib.util.spec_from_file_location("consolidate_archives", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    import sys

    sys.modules["consolidate_archives"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_classify_key_themes():
    m = _load()
    assert m.classify("SST_fermat_pybind_research_v0.6.1.zip")[0] == "Fermat"
    assert m.classify("SST_routeB_RT_bem_research_v18.zip")[0] == "RouteB_BEM"
    assert m.classify("sst_chi_phase_package_v16B0.zip")[0] == "ChiPhase"
    assert m.classify("vortexring-lab-v7.6.22-package.zip")[0] == "VortexLab"
    assert m.classify("SST_CANON-v0.8.23-release.zip")[0] == "Canon"
    assert m.classify("SST_Route_I_relative_entropy_PoC_v0.1.0.zip")[0] == "Route_I"
    assert m.classify("SST_contact_billiard_hydrodynamic_falsifier_v0.2.0.zip")[0] == (
        "ContactBilliard"
    )
    assert m.classify("triple_gear_blender_package.zip")[0] == "TripleGear"
    assert m.classify("totally_unknown_blob.zip")[0] == "Misc"


def test_classify_fermat_series():
    m = _load()
    theme, series = m.classify("SST_fermat_pybind_research_v0.6.1.zip")
    assert theme == "Fermat"
    assert series == "v0.6.1"


def test_dest_for_with_series():
    m = _load()
    dest = m.dest_for("SST_fermat_pybind_research_v0.6.1.zip", "Fermat", "v0.6.1")
    assert dest == m.RESTORE / "Fermat" / "v0.6.1" / "SST_fermat_pybind_research_v0.6.1.zip"


def test_resolve_collision_identical(tmp_path, monkeypatch):
    m = _load()
    monkeypatch.setattr(m, "RESTORE", tmp_path / "Restore_Archives")
    m.RESTORE.mkdir()
    dest_dir = m.RESTORE / "Fermat"
    dest_dir.mkdir()
    dest = dest_dir / "a.zip"
    src = tmp_path / "a.zip"
    payload = b"same-bytes"
    dest.write_bytes(payload)
    src.write_bytes(payload)
    plan = m.resolve_collision(src, dest, "__from_repo")
    assert plan.action == "delete_duplicate"


def test_resolve_collision_different(tmp_path, monkeypatch):
    m = _load()
    monkeypatch.setattr(m, "RESTORE", tmp_path / "Restore_Archives")
    m.RESTORE.mkdir()
    dest_dir = m.RESTORE / "Fermat"
    dest_dir.mkdir()
    dest = dest_dir / "a.zip"
    src = tmp_path / "a.zip"
    dest.write_bytes(b"old")
    src.write_bytes(b"new-content")
    plan = m.resolve_collision(src, dest, "__from_repo")
    assert plan.action == "move_renamed"
    assert plan.dest.name == "a__from_repo.zip"


def test_resolve_collision_fresh(tmp_path, monkeypatch):
    m = _load()
    monkeypatch.setattr(m, "RESTORE", tmp_path / "Restore_Archives")
    m.RESTORE.mkdir()
    dest = m.RESTORE / "Misc" / "fresh.zip"
    src = tmp_path / "fresh.zip"
    src.write_bytes(b"x")
    plan = m.resolve_collision(src, dest, "__from_repo")
    assert plan.action == "move"
    assert plan.dest == dest


def test_apply_plan_move_and_manifest(tmp_path, monkeypatch):
    m = _load()
    restore = tmp_path / "Restore_Archives"
    restore.mkdir()
    monkeypatch.setattr(m, "WB", tmp_path)
    monkeypatch.setattr(m, "RESTORE", restore)
    monkeypatch.setattr(m, "SOURCES_ZIPS", restore / "Sources_Zips")

    src_dir = tmp_path / "SST_fermat_pybind_research"
    src_dir.mkdir()
    src = src_dir / "SST_fermat_pybind_research_v0.1.zip"
    src.write_bytes(b"fermat-zip")

    theme, series = m.classify(src.name)
    dest = m.dest_for(src.name, theme, series)
    plans = [m.resolve_collision(src, dest, "__from_repo")]
    rows = m.apply_plan(plans, apply=True)
    assert not src.exists()
    assert dest.exists()
    assert dest.read_bytes() == b"fermat-zip"
    assert rows[0]["action"] == "move"
    assert rows[0]["theme"] == "Fermat"

    man = restore / "_MANIFEST.csv"
    m.write_manifest(rows, man)
    assert man.exists()
    text = man.read_text(encoding="utf-8")
    assert "Fermat" in text
