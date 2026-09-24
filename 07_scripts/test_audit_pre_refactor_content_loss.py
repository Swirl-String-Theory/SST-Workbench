"""Tests for pre-refactor content-loss classification."""
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import pytest

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import audit_pre_refactor_content_loss as audit  # noqa: E402


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
    (r / "keep.txt").write_text("keep", encoding="utf-8")
    (r / "moved.txt").write_text("moved-bytes", encoding="utf-8")
    (r / "lost.txt").write_text("gone-bytes", encoding="utf-8")
    (r / "outputs").mkdir()
    (r / "outputs" / "run.bin").write_bytes(b"tmp")
    _git(r, "add", ".")
    _git(r, "commit", "-m", "old")
    return r


def test_is_expected_loss():
    assert audit.is_expected_loss("Fam/outputs/run.json")
    assert audit.is_expected_loss("native.pyd")
    assert not audit.is_expected_loss("Fam/src/main.py")


def test_mapped_path_uses_longest_prefix():
    moves = [("Fam", "01_research/A001"), ("Fam/sub", "01_research/A001/sub")]
    assert audit.mapped_path("Fam/sub/a.py", moves) == "01_research/A001/sub/a.py"
    assert audit.mapped_path("unmapped.py", moves) == "unmapped.py"


def test_rename_is_not_loss(repo: Path):
    _git(repo, "mv", "moved.txt", "renamed.txt")
    _git(repo, "rm", "-f", "lost.txt")
    _git(repo, "rm", "-r", "--", "outputs")
    _git(repo, "commit", "-m", "new")
    old = audit.ls_tree_blobs(repo, "HEAD~1")
    new = audit.ls_tree_blobs(repo, "HEAD")
    result = audit.classify_git_paths(old, new, [])
    lost_paths = {row["old_path"] for row in result["lost"]}
    expected_paths = {row["old_path"] for row in result["expected_loss"]}
    assert "keep.txt" not in lost_paths
    assert "moved.txt" not in lost_paths
    assert result["relocated_by_blob"] >= 1
    assert "lost.txt" in lost_paths
    assert "outputs/run.bin" in expected_paths


def test_remap_path_counts_as_present(repo: Path):
    dest = repo / "01_research" / "keep.txt"
    dest.parent.mkdir(parents=True)
    _git(repo, "mv", "keep.txt", "01_research/keep.txt")
    _git(repo, "commit", "-m", "moved-keep")
    old = audit.ls_tree_blobs(repo, "HEAD~1")
    new = audit.ls_tree_blobs(repo, "HEAD")
    result = audit.classify_git_paths(old, new, [("keep.txt", "01_research/keep.txt")])
    lost_paths = {row["old_path"] for row in result["lost"]}
    assert "keep.txt" not in lost_paths
    assert result["present_after_remap"] >= 1


def test_ignored_manifest_missing_and_present(tmp_path: Path):
    root = tmp_path / "wb"
    root.mkdir(parents=True)
    (root / "kept.dat").write_text("x", encoding="utf-8")
    manifest = tmp_path / "file_manifest.csv"
    with manifest.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "size", "mtime", "tracked", "ignored"])
        w.writeheader()
        w.writerow(
            {"path": "kept.dat", "size": "1", "mtime": "", "tracked": "no", "ignored": "yes"}
        )
        w.writerow(
            {
                "path": "missing.dat",
                "size": "1",
                "mtime": "",
                "tracked": "no",
                "ignored": "yes",
            }
        )
        w.writerow(
            {
                "path": "outputs/gone.bin",
                "size": "1",
                "mtime": "",
                "tracked": "no",
                "ignored": "yes",
            }
        )
    report = audit.classify_ignored_manifest(root, [], manifest_path=manifest)
    assert report["present_on_disk"] == 1
    assert report["expected_missing"] == 1
    assert report["unexpected_missing"] == 1
    assert report["unexpected_missing_sample"][0]["old_path"] == "missing.dat"
