"""Tests for 07_scripts/move_phase.py (SP04 mover)."""
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import pytest

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import move_phase  # noqa: E402


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "core.longpaths=true", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )


def _write_path_map(repo: Path, rows: list[dict[str, str]]) -> None:
    fields = [
        "old_path", "new_path", "domain", "letter", "catalog_id",
        "kind", "phase", "junction", "status", "note",
    ]
    pm = repo / "10_docs" / "migration" / "path_map.csv"
    pm.parent.mkdir(parents=True, exist_ok=True)
    with pm.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def _read_path_map(repo: Path) -> list[dict[str, str]]:
    pm = repo / "10_docs" / "migration" / "path_map.csv"
    with pm.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "wb"
    r.mkdir()
    (r / ".sst-workbench-root").write_text("catalog_schema: 1\n", encoding="utf-8")
    _git(r, "init")
    _git(r, "config", "user.email", "sp04@test.local")
    _git(r, "config", "user.name", "SP04 Test")
    _git(r, "config", "core.longpaths", "true")
    return r


def _commit_all(repo: Path) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "seed")


def test_simple_directory_move(repo: Path):
    src = repo / "OldRoot"
    src.mkdir()
    (src / "a.txt").write_text("hello\n", encoding="utf-8")
    _write_path_map(repo, [{
        "old_path": "OldRoot", "new_path": "08_third_party/newroot",
        "phase": "SP04", "junction": "yes", "status": "pending",
    }])
    _commit_all(repo)

    assert move_phase.run_phase(repo, "SP04", dry_run=False) == 0
    assert (repo / "08_third_party" / "newroot" / "a.txt").read_text() == "hello\n"
    assert not src.exists()
    assert _read_path_map(repo)[0]["status"] == "moved"


def test_dry_run_moves_nothing(repo: Path):
    src = repo / "OldRoot"
    src.mkdir()
    (src / "a.txt").write_text("x\n", encoding="utf-8")
    _write_path_map(repo, [{
        "old_path": "OldRoot", "new_path": "06_templates/old",
        "phase": "SP04", "junction": "yes", "status": "pending",
    }])
    _commit_all(repo)

    assert move_phase.run_phase(repo, "SP04", dry_run=True) == 0
    assert src.exists()
    assert _read_path_map(repo)[0]["status"] == "pending"


def test_merge_into_existing_directory(repo: Path):
    """scripts/ -> 07_scripts/ must merge, not nest."""
    src = repo / "scripts"
    src.mkdir()
    (src / "tool.py").write_text("t\n", encoding="utf-8")
    dst = repo / "07_scripts"
    dst.mkdir()
    (dst / "existing.py").write_text("e\n", encoding="utf-8")
    _write_path_map(repo, [{
        "old_path": "scripts", "new_path": "07_scripts",
        "phase": "SP04", "junction": "yes", "status": "pending",
    }])
    _commit_all(repo)

    assert move_phase.run_phase(repo, "SP04", dry_run=False) == 0
    assert (dst / "tool.py").is_file()
    assert (dst / "existing.py").is_file()
    assert not (dst / "scripts").exists(), "source nested instead of merging"
    assert not src.exists()


def test_glob_move(repo: Path):
    for name in ("one.zip", "two.zip"):
        (repo / name).write_text("z\n", encoding="utf-8")
    (repo / "keep.txt").write_text("k\n", encoding="utf-8")
    _write_path_map(repo, [{
        "old_path": "*.zip", "new_path": "09_archive/restore/root_zips",
        "phase": "SP04", "junction": "no", "status": "pending",
    }])
    _commit_all(repo)

    assert move_phase.run_phase(repo, "SP04", dry_run=False) == 0
    assert (repo / "09_archive/restore/root_zips/one.zip").is_file()
    assert (repo / "09_archive/restore/root_zips/two.zip").is_file()
    assert (repo / "keep.txt").is_file()


def test_untracked_directory_falls_back_to_fs_move(repo: Path):
    (repo / ".gitignore").write_text("ignored/\n", encoding="utf-8")
    _commit_all(repo)
    src = repo / "ignored"
    src.mkdir()
    (src / "blob.bin").write_text("b\n", encoding="utf-8")
    _write_path_map(repo, [{
        "old_path": "ignored", "new_path": "09_archive/ignored",
        "phase": "SP04", "junction": "no", "status": "pending",
    }])

    assert move_phase.run_phase(repo, "SP04", dry_run=False) == 0
    assert (repo / "09_archive/ignored/blob.bin").is_file()
    assert not src.exists()


def test_missing_source_is_skipped_not_failed(repo: Path):
    _write_path_map(repo, [{
        "old_path": "DoesNotExist", "new_path": "09_archive/nope",
        "phase": "SP04", "junction": "no", "status": "pending",
    }])
    _commit_all(repo)

    assert move_phase.run_phase(repo, "SP04", dry_run=False) == 0
    row = _read_path_map(repo)[0]
    assert row["status"] == "skipped"
    assert "old_path_missing_on_disk" in row["note"]


def test_delete_destination_is_an_ordinary_move(repo: Path):
    """DELETE/ rows preserve the path from repo root and never unlink."""
    src = repo / "to_be_processed"
    src.mkdir()
    (src / "README.md").write_text("stub\n", encoding="utf-8")
    _write_path_map(repo, [{
        "old_path": "to_be_processed", "new_path": "DELETE/to_be_processed",
        "phase": "SP11", "junction": "no", "status": "pending",
    }])
    _commit_all(repo)

    assert move_phase.run_phase(repo, "SP11", dry_run=False) == 0
    assert (repo / "DELETE/to_be_processed/README.md").read_text() == "stub\n"
    assert not src.exists()


def test_other_phases_untouched(repo: Path):
    (repo / "A").mkdir()
    (repo / "A" / "f.txt").write_text("a\n", encoding="utf-8")
    (repo / "B").mkdir()
    (repo / "B" / "f.txt").write_text("b\n", encoding="utf-8")
    _write_path_map(repo, [
        {"old_path": "A", "new_path": "06_templates/a", "phase": "SP04",
         "junction": "no", "status": "pending"},
        {"old_path": "B", "new_path": "06_templates/b", "phase": "SP05",
         "junction": "no", "status": "pending"},
    ])
    _commit_all(repo)

    assert move_phase.run_phase(repo, "SP04", dry_run=False) == 0
    assert (repo / "06_templates/a/f.txt").is_file()
    assert (repo / "B" / "f.txt").is_file(), "SP05 row must not move"


def test_verify_marks_rows_verified(repo: Path):
    src = repo / "OldRoot"
    src.mkdir()
    (src / "a.txt").write_text("hello\n", encoding="utf-8")
    _write_path_map(repo, [{
        "old_path": "OldRoot", "new_path": "08_third_party/newroot",
        "phase": "SP04", "junction": "yes", "status": "pending",
    }])
    _commit_all(repo)

    move_phase.run_phase(repo, "SP04", dry_run=False)
    assert move_phase.verify_phase(repo, "SP04") == 0
    assert _read_path_map(repo)[0]["status"] == "verified"
