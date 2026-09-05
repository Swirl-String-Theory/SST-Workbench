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


def test_family_legacy_root_is_a_single_component():
    fam = next(f for f in cm.discover() if f.catalog_id == "A042" and f.domain == "01_research")
    assert vr.family_legacy_root(fam) == "SST_Quantum_Galileo_Action_Gauge_Closure"
