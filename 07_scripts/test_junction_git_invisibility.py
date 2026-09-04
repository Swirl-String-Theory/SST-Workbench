"""Regression: junctions must not appear as untracked trees to git (SP02)."""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import junctions as jn  # noqa: E402

pytestmark = pytest.mark.skipif(os.name != "nt", reason="junctions need Windows")


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )


def test_junction_invisible_to_git_status(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".sst-workbench-root").write_text("catalog_schema: 1\n", encoding="utf-8")
    (root / "10_docs" / "migration").mkdir(parents=True)

    _git(root, "init")
    _git(root, "config", "user.email", "sp02@test.local")
    _git(root, "config", "user.name", "SP02 Test")

    # Track content at the *old* path, then simulate move to new_path.
    old = root / "KnotPlotLite"
    old.mkdir()
    payload = old / "knots" / "final" / "a.txt"
    payload.parent.mkdir(parents=True)
    payload.write_text("knot-data\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "seed")

    new = root / "03_data" / "A_knots" / "A001_knotplot_relaxed"
    new.parent.mkdir(parents=True)
    # git mv simulation
    _git(root, "mv", "KnotPlotLite", str(new.relative_to(root)).replace("\\", "/"))
    _git(root, "commit", "-m", "move pack")

    fields = [
        "old_path",
        "new_path",
        "domain",
        "letter",
        "catalog_id",
        "kind",
        "phase",
        "junction",
        "status",
        "note",
    ]
    with (root / "10_docs" / "migration" / "path_map.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerow(
            {
                "old_path": "KnotPlotLite",
                "new_path": "03_data/A_knots/A001_knotplot_relaxed",
                "phase": "SP04",
                "junction": "yes",
                "status": "moved",
            }
        )

    # Without exclude, a junction would look like thousands of untracked files.
    assert jn.main(["--root", str(root), "create"]) == 0
    assert jn.is_junction(root / "KnotPlotLite")

    status = _git(root, "status", "--porcelain").stdout
    # Junction must not introduce untracked paths under the old name.
    bad = [
        ln
        for ln in status.splitlines()
        if "KnotPlotLite" in ln and ln.startswith("??")
    ]
    assert bad == [], f"junction leaked into git status:\n{status}"

    # Reachability through the old hardcoded path still works.
    assert (root / "KnotPlotLite" / "knots" / "final" / "a.txt").read_text(
        encoding="utf-8"
    ) == "knot-data\n"
