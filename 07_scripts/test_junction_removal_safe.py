"""SP11: junction removal must never delete the target tree."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import junctions as jn  # noqa: E402
import sp11_decommission as sp11  # noqa: E402

pytestmark = pytest.mark.skipif(os.name != "nt", reason="junctions need Windows")


def _init_scratch(tmp_path: Path) -> Path:
    (tmp_path / ".sst-workbench-root").write_text("catalog_schema: 1\n", encoding="utf-8")
    (tmp_path / "10_docs" / "migration").mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "sp11@test.local"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "SP11 Test"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    exclude = tmp_path / ".git" / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    exclude.write_text("", encoding="utf-8")
    return tmp_path


def test_remove_junction_preserves_target_file_count(tmp_path: Path):
    root = _init_scratch(tmp_path)
    target = root / "01_research" / "A_falsifiers" / "A999" / "A999-v0.1.0"
    target.mkdir(parents=True)
    payload = [f"f{i}.txt" for i in range(5)]
    for name in payload:
        (target / name).write_text(f"{name}\n", encoding="utf-8")
    nested = target / "nested"
    nested.mkdir()
    (nested / "deep.bin").write_bytes(b"\x00\x01\x02")

    before = sum(1 for p in target.rglob("*") if p.is_file())
    link = root / "LegacyA999"
    jn.create_junction(link, target)
    jn.upsert_registry(root, old_path="LegacyA999", target=target, phase="SP11")
    jn.ensure_git_exclude(root, "LegacyA999")

    stats = sp11.remove_live_junctions(root, dry_run=False)
    assert stats["errors"] == 0
    assert stats["junctions_removed"] == 1
    assert not link.exists()
    assert not jn.is_junction(link)
    after = sum(1 for p in target.rglob("*") if p.is_file())
    assert after == before == 6
    assert (target / "f0.txt").read_text(encoding="utf-8") == "f0.txt\n"
    assert (root / "10_docs" / "migration" / "junction_registry_pre_sp11.csv").is_file()
    # Provenance registry kept (not wiped by SP11 helper).
    assert any(
        (r.get("old_path") or "").replace("\\", "/") == "LegacyA999"
        for r in jn.load_registry(root)
    )


def test_empty_scaffold_removed_after_child_junctions(tmp_path: Path):
    root = _init_scratch(tmp_path)
    target = root / "01_research" / "pack"
    target.mkdir(parents=True)
    (target / "marker.txt").write_text("ok\n", encoding="utf-8")
    scaffold = root / "SharedContainer"
    scaffold.mkdir()
    child = scaffold / "v0.1.0"
    jn.create_junction(child, target)
    jn.upsert_registry(root, old_path="SharedContainer/v0.1.0", target=target, phase="SP11")
    jn.upsert_registry(
        root, old_path="SharedContainer", target=scaffold, phase="SP11"
    )

    stats = sp11.remove_live_junctions(root, dry_run=False)
    assert stats["errors"] == 0
    assert stats["junctions_removed"] == 1
    assert stats["scaffolds_removed"] == 1
    assert not scaffold.exists()
    assert (target / "marker.txt").read_text(encoding="utf-8") == "ok\n"
