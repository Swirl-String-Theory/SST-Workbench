"""SP03: root marker + longpaths hygiene."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import sst_workbench_paths as swp  # noqa: E402


def test_root_marker_exists_and_parses():
    marker = WB / ".sst-workbench-root"
    assert marker.is_file()
    text = marker.read_text(encoding="utf-8")
    assert "catalog_schema: 1" in text


def test_marker_found_from_four_depths(monkeypatch):
    monkeypatch.delenv("SST_WORKBENCH_ROOT", raising=False)
    starts = [
        WB,
        WB / "07_scripts",
        WB / "07_scripts" / "sst_workbench_paths",
        WB / "10_docs" / "migration",
        WB / "01_research" / "A_falsifiers",
    ]
    for start in starts:
        assert start.exists(), start
        assert swp.find_workbench_root(start=start) == WB.resolve()


def test_core_longpaths_enabled():
    proc = subprocess.run(
        ["git", "config", "--get", "core.longpaths"],
        cwd=WB,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip().lower() == "true"


@pytest.mark.skipif(os.name != "nt", reason="Windows long-path checkout check")
def test_long_path_create_and_checkout(tmp_path: Path):
    """core.longpaths must allow create + checkout beyond legacy MAX_PATH."""
    repo = tmp_path / "longrepo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "core.longpaths", "true"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "sp03@test.local"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "SP03 Test"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Build a relative path whose absolute form exceeds 260 chars.
    parts = ["d"] * 80
    rel = Path(*parts) / ("f" * 80 + ".txt")
    full = repo / rel
    assert len(str(full)) > 260, len(str(full))
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text("long-path-ok\n", encoding="utf-8")

    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "long path"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Fresh checkout into a sibling work tree directory via clone of local repo
    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", str(repo), str(clone)],
        check=True,
        capture_output=True,
    )
    cloned = clone / rel
    assert cloned.is_file()
    assert cloned.read_text(encoding="utf-8") == "long-path-ok\n"
