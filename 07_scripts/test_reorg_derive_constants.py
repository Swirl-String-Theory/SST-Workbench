"""Unit tests for reorg_derive_constants helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).with_name("reorg_derive_constants.py")


def _load():
    spec = importlib.util.spec_from_file_location("reorg_derive_constants", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def reorg():
    return _load()


def test_version_folder_for_bem_script(reorg):
    assert (
        reorg.version_folder_for_bem_script("routeB_RT_bem_v14_certified_convergence.py")
        == "SST_routeB_RT_bem_research_v14"
    )
    assert (
        reorg.version_folder_for_bem_script("routeB_RT_bem_v3_1_sstcore_falsifier.py")
        == "SST_routeB_RT_bem_research_v3_1"
    )
    assert (
        reorg.version_folder_for_bem_script("README_routeB_RT_bem_stecklov_falsifier.md")
        == "SST_routeB_RT_bem_research_stecklov"
    )
    assert reorg.version_folder_for_bem_script("bem_scale_roles.py") is None


def test_output_version_key(reorg):
    assert (
        reorg.output_version_key("outputs_routeB_BEM_v14_stageA")
        == "SST_routeB_RT_bem_research_v14"
    )
    assert (
        reorg.output_version_key("outputs_routeB_BEM_v9 _demo")
        == "SST_routeB_RT_bem_research_v9"
    )
    assert reorg.output_version_key("outputs_v16") == "SST_routeB_RT_bem_research_v16"
    assert reorg.output_version_key("outputs_routeB_SSTcore_all20") == "legacy"
    assert reorg.output_version_key("demo_outputs_current_ideal_v19") == "legacy"


def test_bridge_version_dir(reorg):
    assert (
        reorg.bridge_version_dir("sst_contra_swirl_bridge_test.py")
        == "SST_contra_swirl_bridge_research_v0"
    )
    assert (
        reorg.bridge_version_dir("sst_contra_swirl_bridge_test_v0_2.py")
        == "SST_contra_swirl_bridge_research_v0_2"
    )
    assert (
        reorg.bridge_version_dir(
            "sst_contra_swirl_bridge_test_v0_6_timefield_supplement_audit.py"
        )
        == "SST_contra_swirl_bridge_research_v0_6"
    )


def test_is_timefield_and_fs(reorg):
    assert reorg.is_timefield_name("v06_timefield_ratio_cv.png")
    assert reorg.is_timefield_name("canon_spectral_summary.md")
    assert not reorg.is_timefield_name("hopfion_tools.py")
    assert reorg.is_fs_name("gear_locked_attachment_audit_summary.md")
    assert reorg.is_fs_name("README_MAXHR_unified_attachment_audit.md")
    assert not reorg.is_fs_name("ideal.txt")


def test_count_files(tmp_path, reorg):
    d = tmp_path / "a"
    d.mkdir()
    (d / "f.txt").write_text("x", encoding="utf-8")
    sub = d / "sub"
    sub.mkdir()
    (sub / "g.txt").write_text("y", encoding="utf-8")
    assert reorg.count_files(d) == 2
    assert reorg.count_files(d / "f.txt") == 1
    assert reorg.count_files(tmp_path / "missing") == 0
