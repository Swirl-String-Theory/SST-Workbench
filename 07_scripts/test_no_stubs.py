"""SP11: relocation stubs must be soft-retired under DELETE/."""

from __future__ import annotations

import sys
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import sp11_decommission as sp11  # noqa: E402

STUBS = sp11.STUB_PATHS


def test_stub_paths_absent_at_repo_root():
    present = sp11.stubs_absent(WB)
    assert present == [], f"stubs still at root: {present}"


def test_stubs_live_under_delete():
    for rel in STUBS:
        dest = WB / "DELETE" / rel.replace("\\", "/")
        assert dest.is_dir(), f"missing DELETE landing: {dest}"
        readmes = list(dest.rglob("README.md"))
        assert readmes, f"expected README under {dest}"


def test_falsifier_registry_yaml_stays_at_root():
    assert (WB / "falsifier_registry.yaml").is_file()
