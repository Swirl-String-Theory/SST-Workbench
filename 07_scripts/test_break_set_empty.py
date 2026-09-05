"""SP11: break-set acceptance — stubs gone; catalogs reachable without junctions."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import sp11_decommission as sp11  # noqa: E402

# Explicit accept-list for lingering documentary / historical path strings.
# Runtime resolvers must use catalog paths; these docs may still mention legacy names.
ACCEPTED_LEGACY_MENTIONS = {
    "10_docs/migration/MIGRATION_MANIFEST.md",
    "10_docs/migration/MOVE_DERIVE_CONSTANTS_MANIFEST.md",
    "10_docs/migration/path_map.csv",
    "10_docs/migration/junction_registry.csv",
    "10_docs/migration/junction_registry_pre_sp11.csv",
    "10_docs/migration/sp11_decommission.md",
    "10_docs/migration/sp11_husk_cleanup.md",
    "10_docs/migration/reproducibility_gate.md",
    ".cursor/plans/restructure",
}


def test_domain_roots_exist():
    for rel in (
        "01_research",
        "02_libraries",
        "03_data",
        "04_tools",
        "05_apps",
        "07_scripts",
        "09_archive",
        "10_docs",
    ):
        assert (WB / rel).is_dir(), rel


def test_no_stub_break_paths():
    assert sp11.stubs_absent(WB) == []


def test_catalog_index_present():
    idx = WB / "10_docs" / "registry" / "catalog_index.json"
    assert idx.is_file()


def test_path_map_sp11_stubs_verified():
    path = WB / "10_docs" / "migration" / "path_map.csv"
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    stub_olds = set(sp11.STUB_PATHS)
    found = set()
    for r in rows:
        old = r["old_path"].replace("\\", "/")
        if old in stub_olds:
            found.add(old)
            assert (r.get("status") or "").lower() == "verified"
            assert r["new_path"].replace("\\", "/").startswith("DELETE/")
    assert found == stub_olds


def test_no_live_root_junctions_after_sp11():
    assert sp11.live_root_junctions(WB) == []
