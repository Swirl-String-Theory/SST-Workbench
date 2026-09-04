"""Tests for scripts/migration_manifest.py."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).with_name("migration_manifest.py")


def _load():
    spec = importlib.util.spec_from_file_location("migration_manifest", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _git_init_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "test"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    (root / "tracked.txt").write_text("hello\n", encoding="utf-8")
    (root / ".gitignore").write_text("ignored.bin\n.gitkeep_ignored/\n", encoding="utf-8")
    (root / "ignored.bin").write_bytes(b"x" * 1_500_000)
    (root / "small_ignored.bin").write_bytes(b"y" * 10)
    # gitignore covers ignored.bin and small via pattern - only ignored.bin in gitignore
    # add small_ignored to gitignore too
    (root / ".gitignore").write_text("ignored.bin\nsmall_ignored.bin\n", encoding="utf-8")
    (root / ".tmp.driveupload").mkdir()
    (root / ".tmp.driveupload" / "staging.dat").write_bytes(b"z" * 100)
    (root / ".git_should_skip_via_walk").mkdir()  # not .git
    subprocess.run(["git", "add", "tracked.txt", ".gitignore"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=root, check=True, capture_output=True)
    return root


def test_manifest_excludes_git_and_driveupload(tmp_path: Path):
    m = _load()
    root = _git_init_fixture(tmp_path)
    rows = m.build_manifest(root)
    paths = {r["path"] for r in rows}
    assert "tracked.txt" in paths
    assert not any(p.startswith(".git/") for p in paths)
    assert not any(p.startswith(".tmp.driveupload") for p in paths)


def test_tracked_ignored_flags_match_git(tmp_path: Path):
    m = _load()
    root = _git_init_fixture(tmp_path)
    rows = {r["path"]: r for r in m.build_manifest(root)}
    assert rows["tracked.txt"]["tracked"] == "yes"
    assert rows["tracked.txt"]["ignored"] == "no"
    assert rows["ignored.bin"]["tracked"] == "no"
    assert rows["ignored.bin"]["ignored"] == "yes"
    assert rows["small_ignored.bin"]["ignored"] == "yes"


def test_checksums_cover_tracked_and_large_ignored(tmp_path: Path):
    m = _load()
    root = _git_init_fixture(tmp_path)
    rows = m.build_manifest(root)
    entries = m.build_checksums(root, rows, min_ignored_bytes=1_000_000)
    by_path = {p: d for d, p in entries}
    assert "tracked.txt" in by_path
    assert "ignored.bin" in by_path  # >1MB ignored
    assert "small_ignored.bin" not in by_path
    # digest is 64 hex chars
    assert len(by_path["tracked.txt"]) == 64
