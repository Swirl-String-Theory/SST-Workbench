"""Tests for Google Drive `` (N)`` conflict classification and cleanup."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import cleanup_drive_conflict_copies as drv  # noqa: E402


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "core.longpaths=true", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "wb"
    r.mkdir()
    _git(r, "init")
    _git(r, "config", "user.email", "test@example.com")
    _git(r, "config", "user.name", "Test")
    (r / "keep.txt").write_text("same", encoding="utf-8")
    (r / "tracked (1).txt").write_text("historical", encoding="utf-8")
    _git(r, "add", "keep.txt", "tracked (1).txt")
    _git(r, "commit", "-m", "init")
    return r


def test_drive_canonical_component_file_and_dir():
    assert drv.drive_canonical_component("run_all (1).cmd") == "run_all.cmd"
    assert drv.drive_canonical_component(".gitignore (1)") == ".gitignore"
    assert drv.drive_canonical_component("SST_Template_v0.1.0 (1)") == "SST_Template_v0.1.0"
    assert drv.drive_canonical_component("Infographic(1).png") is None
    assert drv.drive_canonical_component("keep.txt") is None


def test_canonical_rel_strips_folder_and_file():
    rel = "06_templates/SST_Template_v0.1.0 (1)/run_all (2).cmd"
    assert drv.canonical_rel(rel) == "06_templates/SST_Template_v0.1.0/run_all.cmd"


def test_has_drive_conflict_component():
    assert drv.has_drive_conflict_component("foo (1).py")
    assert drv.has_drive_conflict_component("dir (1)/readme.md")
    assert not drv.has_drive_conflict_component("Infographic(1).png")


def test_hash_match_delete_and_unique_quarantine(repo: Path):
    (repo / "keep (1).txt").write_text("same", encoding="utf-8")
    (repo / "only (1).txt").write_text("unique-bytes", encoding="utf-8")
    pack = repo / "pack (1)"
    pack.mkdir()
    (pack / "inside.txt").write_text("unique-inside", encoding="utf-8")
    actions = drv.classify_tree(repo)
    by_rel = {a.rel: a for a in actions}
    assert by_rel["keep (1).txt"].action == "delete_duplicate"
    assert by_rel["only (1).txt"].action == "quarantine_unique"
    assert by_rel["pack (1)/inside.txt"].action == "quarantine_unique"
    assert "tracked (1).txt" not in by_rel
    ledger = repo / "ledger.jsonl"
    counts = drv.apply_actions(repo, actions, apply=True, ledger=ledger)
    assert counts["delete_duplicate"] == 1
    assert counts["quarantine_unique"] == 2
    assert not (repo / "keep (1).txt").exists()
    assert (repo / "keep.txt").read_text(encoding="utf-8") == "same"
    q = repo / drv.QUARANTINE
    assert (q / "only (1).txt").read_text(encoding="utf-8") == "unique-bytes"
    assert (q / "pack (1)" / "inside.txt").read_text(encoding="utf-8") == "unique-inside"
    assert not (repo / "pack (1)").exists()
    assert ledger.is_file()


def test_skip_tracked_conflict_name(repo: Path):
    action = drv.classify_conflict(
        repo, "tracked (1).txt", tracked=drv.tracked_paths(repo)
    )
    assert action.action == "skip_tracked"


def test_already_quarantined_is_skipped(repo: Path):
    q = repo / drv.QUARANTINE / "keep (1).txt"
    q.parent.mkdir(parents=True)
    q.write_text("unique", encoding="utf-8")
    actions = drv.classify_tree(repo)
    assert all(not a.rel.startswith(drv.QUARANTINE.as_posix()) for a in actions)
    (repo / "keep (1).txt").write_text("same", encoding="utf-8")
    actions = drv.classify_tree(repo)
    drv.apply_actions(repo, actions, apply=False, ledger=None)
    assert (repo / "keep (1).txt").exists()


def test_remove_empty_parents_swallows_oserror(tmp_path: Path, monkeypatch):
    root = tmp_path / "wb"
    nested = root / "a (1)" / "b"
    nested.mkdir(parents=True)
    calls = {"n": 0}

    def boom(self):
        calls["n"] += 1
        raise PermissionError("locked")

    monkeypatch.setattr(Path, "rmdir", boom)
    drv._remove_empty_parents(nested, root)
    assert calls["n"] == 1
