"""Tests for workbench_tree.py."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).with_name("workbench_tree.py")


def _load():
    spec = importlib.util.spec_from_file_location("workbench_tree", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_parse_version_tuple():
    m = _load()
    assert m.parse_version_tuple("SST_fermat_pybind_research_v0.6.1") == (0, 6, 1)
    assert m.parse_version_tuple("SST_routeB_RT_bem_research_v3_1") == (3, 1)
    assert m.parse_version_tuple("README") is None


def test_version_token_and_is_version_dir_name():
    m = _load()
    assert m.version_token("SST_fermat_pybind_research_v0.6.1") == "v0.6.1"
    assert m.version_token("sst_chi_phase_package_v16B0") == "v16B0"
    assert m.version_token(
        "SST_ideal_links_comprehensive_test_suite_v0.4.0-alpha.1"
    ) == "v0.4.0-alpha.1"
    assert m.version_token("demos") is None
    assert m.is_version_dir_name("pack_v0.1.0")
    assert not m.is_version_dir_name("scripts")


def test_folder_dates_has_created_and_modified(tmp_path: Path):
    m = _load()
    d = tmp_path / "pack"
    d.mkdir()
    dates = m.folder_dates(d)
    assert "created" in dates and "T" in dates["created"]
    assert "modified" in dates and "T" in dates["modified"]


def test_scan_groups_versions_under_family(tmp_path: Path):
    m = _load()
    fam = tmp_path / "SST_fermat_pybind_research"
    (fam / "SST_fermat_pybind_research_v0.1").mkdir(parents=True)
    (fam / "SST_fermat_pybind_research_v0.6.1").mkdir()
    (fam / "docs").mkdir()
    (fam / "docs" / "notes.md").write_text("x", encoding="utf-8")

    tree = m.scan_workbench(tmp_path, max_depth=3)
    node = tree["SST_fermat_pybind_research"]
    assert set(node["versions"]) == {"v0.1", "v0.6.1"}
    assert node["latest"] == "v0.6.1"
    assert node["versions"]["v0.6.1"]["name"] == "SST_fermat_pybind_research_v0.6.1"
    assert "docs" in node["folders"]
    assert node["folders"]["docs"]["file_count"] == 1


def test_nested_family_versions(tmp_path: Path):
    m = _load()
    lib = tmp_path / "Knot_Library" / "SST_Knot_Library"
    (lib / "SST_Knot_Library_v0.2.0").mkdir(parents=True)
    (lib / "SST_Knot_Library_v0.2.4").mkdir()
    (tmp_path / "Knot_Library" / "Registry").mkdir()

    tree = m.scan_workbench(tmp_path, max_depth=3)
    knot = tree["Knot_Library"]
    nested = knot["folders"]["SST_Knot_Library"]
    assert nested["latest"] == "v0.2.4"
    assert set(nested["versions"]) == {"v0.2.0", "v0.2.4"}
    assert "Registry" in knot["folders"]


def test_duplicate_version_tokens_use_full_name(tmp_path: Path):
    m = _load()
    fam = tmp_path / "SST_chi_phase_research"
    (fam / "sst_chi_phase_package_v16B0").mkdir(parents=True)
    (fam / "other_lineage_v16B0").mkdir()

    tree = m.scan_workbench(tmp_path, max_depth=2)
    versions = tree["SST_chi_phase_research"]["versions"]
    names = {meta["name"] for meta in versions.values()}
    assert names == {"sst_chi_phase_package_v16B0", "other_lineage_v16B0"}
    assert "v16B0" in versions
    assert any(key.endswith("v16B0") and key != "v16B0" for key in versions)


def test_skips_dot_dirs_and_limits_heavy_trees(tmp_path: Path):
    m = _load()
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "secret_v0.1.0").mkdir()
    (tmp_path / "media" / "deep" / "SST_pack_v0.9").mkdir(parents=True)
    (tmp_path / "Restore_Archives" / "Fermat").mkdir(parents=True)
    (tmp_path / "Restore_Archives" / "Fermat" / "nested").mkdir()
    (tmp_path / "GUI" / "vortexring-lab").mkdir(parents=True)
    (tmp_path / "KnotPlot" / "knots" / "knot_3.1").mkdir(parents=True)
    (tmp_path / "KnotPlot" / "Campaign_v0.1.0").mkdir()

    tree = m.scan_workbench(tmp_path, max_depth=3)
    assert ".git" not in tree
    assert tree["media"]["folders"]["deep"]["path"] == "media/deep"
    assert "versions" not in tree["media"]["folders"]["deep"]
    assert "folders" not in tree["media"]["folders"]["deep"]
    assert "Fermat" in tree["Restore_Archives"]["folders"]
    assert "folders" not in tree["Restore_Archives"]["folders"]["Fermat"]
    assert tree["GUI"]["folders"]["vortexring-lab"]["path"] == "GUI/vortexring-lab"
    assert "v0.1.0" in tree["KnotPlot"]["versions"]
    assert "versions" not in tree["KnotPlot"]["folders"]["knots"]
    assert "knot_3.1" not in (tree["KnotPlot"]["folders"]["knots"].get("folders") or {})


def test_build_and_write_inventory(tmp_path: Path):
    m = _load()
    fam = tmp_path / "SST_Hopf_Benchmark"
    (fam / "SST_Hopf_cpp_pybind_v0.1.3").mkdir(parents=True)
    out = tmp_path / "INVENTORY_TREE.json"
    payload = m.build_inventory(tmp_path, max_depth=2)
    written = m.write_inventory(payload, out)
    data = json.loads(written.read_text(encoding="utf-8"))
    assert data["family_count"] == 1
    assert data["version_count"] == 1
    assert data["tree"]["SST_Hopf_Benchmark"]["latest"] == "v0.1.3"


def test_main_writes_default_shaped_json(tmp_path: Path):
    m = _load()
    (tmp_path / "scripts").mkdir()
    out = tmp_path / "tree.json"
    rc = m.main(["--root", str(tmp_path), "--out", str(out), "--max-depth", "2"])
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "scripts" in data["tree"]
    assert data["tree"]["scripts"]["dir_count"] == 0
