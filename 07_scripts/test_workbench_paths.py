"""Tests for 07_scripts/sst_workbench_paths resolution order."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import sst_workbench_paths as swp  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    for key in (
        "SST_WORKBENCH_ROOT",
        "SST_DATA_ROOT",
        "SST_KNOT_DATASET",
        "SST_IDEAL_SOURCES",
        "SST_KATLAS_SOURCES",
        "SST_FSERIES_ROOT",
    ):
        monkeypatch.delenv(key, raising=False)


def test_marker_file_exists_at_repo_root():
    assert (WB / swp.ROOT_MARKER).is_file()


def test_workbench_root_from_module_location():
    root = swp.workbench_root()
    assert root == WB.resolve()
    assert (root / swp.ROOT_MARKER).is_file()


def test_workbench_root_from_nested_start(tmp_path):
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    # Walk from a path inside the real workbench (catalog path; SP11 removed
    # the ``scripts`` junction).
    deep = WB / "07_scripts"
    root = swp.workbench_root(start=deep)
    assert root == WB.resolve()


def test_env_override_wins(monkeypatch, tmp_path):
    marker = tmp_path / swp.ROOT_MARKER
    marker.write_text("catalog_schema: 1\n", encoding="utf-8")
    monkeypatch.setenv("SST_WORKBENCH_ROOT", str(tmp_path))
    assert swp.workbench_root() == tmp_path.resolve()


def test_missing_marker_raises(monkeypatch, tmp_path):
    orphan = tmp_path / "orphan"
    orphan.mkdir()
    monkeypatch.delenv("SST_WORKBENCH_ROOT", raising=False)
    with pytest.raises(swp.WorkbenchRootNotFound):
        swp.find_workbench_root(start=orphan, explicit=None)


def test_explicit_without_marker_raises(tmp_path):
    with pytest.raises(swp.WorkbenchRootNotFound):
        swp.find_workbench_root(explicit=tmp_path)


def test_data_root_default_and_override(monkeypatch):
    assert swp.data_root() == (WB / "03_data").resolve()
    monkeypatch.setenv("SST_DATA_ROOT", str(WB / "07_scripts"))
    assert swp.data_root() == (WB / "07_scripts").resolve()


def test_knot_dataset_prefers_catalog_path():
    kd = swp.knot_dataset()
    assert kd == (WB / "03_data" / "A_knots" / "04_knotplot" / "final").resolve()
    assert kd.is_dir()


def test_ideal_sources_prefers_catalog_path():
    assert swp.ideal_sources() == (
        WB / "03_data" / "A_knots" / "01_ideal" / "ideal_sources"
    ).resolve()
    assert swp.ideal_sources().is_dir()


def test_module_level_aliases_match_functions():
    assert swp.WORKBENCH_ROOT == swp.workbench_root()
    assert swp.DATA_ROOT == swp.data_root()
    assert swp.KNOT_DATASET == swp.knot_dataset()
    assert swp.IDEAL_SOURCES == swp.ideal_sources()
