"""Tests for resolve_family against path_map.csv."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import sst_workbench_paths as swp  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    monkeypatch.delenv("SST_WORKBENCH_ROOT", raising=False)


def test_known_falsifier_resolves_to_existing_old_path():
    # Pre-move: old_path still on disk.
    path = swp.resolve_family("A006")
    assert path == (WB / "SST_contact_billiard_hydrodynamic_falsifier").resolve()
    assert path.is_dir()


def test_galileo_a042():
    path = swp.resolve_family("A042")
    assert path.name.startswith("SST_Quantum_Galileo") or "A042_" in path.name
    assert path.is_dir()


def test_unknown_id_raises():
    with pytest.raises(KeyError, match="unknown catalog_id"):
        swp.resolve_family("Z999")


def test_version_selects_subdirectory():
    family = swp.resolve_family("A006")
    versions = sorted(p.name for p in family.iterdir() if p.is_dir())
    assert versions, "expected version dirs under A006 family"
    # Pick a version token present in a directory name
    sample = versions[0]
    # Extract a vX.Y.Z-like token if present
    import re

    m = re.search(r"v\d+(?:\.\d+)+", sample)
    token = m.group(0) if m else sample
    resolved = swp.resolve_family("A006", version=token)
    assert resolved.is_dir()
    assert token in resolved.name


def test_domain_disambiguation_for_shared_ids():
    # A001 exists in research (route_a) and may appear in apps/libraries.
    research = swp.resolve_family("A001", domain="01_research")
    assert "route_a" in research.name or research.name.startswith("SST_v0_8_19")
    # Default preference is 01_research
    default = swp.resolve_family("A001")
    assert default == research


def test_library_b001():
    path = swp.resolve_family("B001", domain="02_libraries")
    assert "FiniteCore" in path.name or "finite_core" in path.as_posix()
    assert path.is_dir()
