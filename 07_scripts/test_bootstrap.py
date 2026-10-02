"""bootstrap_junctions.cmd reconstructs registry rows and passes verify."""

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

BOOTSTRAP = WB / "07_scripts" / "bootstrap_junctions.cmd"

pytestmark = pytest.mark.skipif(os.name != "nt", reason="bootstrap is Windows CMD")


def _scratch_with_moved(tmp_path: Path) -> Path:
    root = tmp_path / "wb"
    root.mkdir()
    (root / ".sst-workbench-root").write_text("catalog_schema: 1\n", encoding="utf-8")
    mig = root / "10_docs" / "migration"
    mig.mkdir(parents=True)
    (mig / "junction_registry.csv").write_text(
        "old_path,target,created_at,phase\n", encoding="utf-8"
    )
    (root / ".git" / "info").mkdir(parents=True)
    (root / ".git" / "info" / "exclude").write_text("", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)

    # Copy junctions.py + bootstrap into scratch 07_scripts so bootstrap's
    # relative root discovery matches a real clone layout.
    scripts = root / "07_scripts"
    scripts.mkdir()
    (scripts / "junctions.py").write_text(
        (WB / "07_scripts" / "junctions.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (scripts / "bootstrap_junctions.cmd").write_text(
        BOOTSTRAP.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    target = root / "03_data" / "A_knots" / "Z001_demo"
    target.mkdir(parents=True)
    (target / "ok.txt").write_text("bootstrap\n", encoding="utf-8")

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
    with (mig / "path_map.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerow(
            {
                "old_path": "DemoPack",
                "new_path": "03_data/A_knots/Z001_demo",
                "phase": "SP04",
                "junction": "yes",
                "status": "moved",
            }
        )
    return root


def test_bootstrap_reconstructs_and_verifies(tmp_path: Path):
    root = _scratch_with_moved(tmp_path)
    bat = root / "07_scripts" / "bootstrap_junctions.cmd"
    proc = subprocess.run(
        ["cmd", "/d", "/c", str(bat)],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr

    link = root / "DemoPack"
    assert jn.is_junction(link)
    assert (link / "ok.txt").read_text(encoding="utf-8") == "bootstrap\n"

    reg = jn.load_registry(root)
    assert len(reg) == 1
    assert reg[0]["old_path"] == "DemoPack"

    assert jn.main(["--root", str(root), "verify"]) == 0


def test_bootstrap_cmd_exists_and_is_documented():
    """Bootstrap remains the official restore path; do not run it on the live tree.

    Pre-SP11 this test executed ``bootstrap_junctions.cmd`` against the real
    workbench under the outdated assumption that there were no selectable
    junction rows. After SP04–SP10 those rows exist (status moved/verified), so
    a live bootstrap recreates the entire compat layer — which undoes SP11.
    """
    assert BOOTSTRAP.is_file()
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert "junctions.py" in text
    assert "create" in text


def test_live_workbench_create_dry_run_only():
    """Dry-run may list rows; must not create junctions on the live tree."""
    before = {
        r["old_path"]
        for r in jn.load_registry(WB)
        if jn.is_junction(WB / (r.get("old_path") or "").replace("\\", "/"))
    }
    assert jn.main(["--root", str(WB), "create", "--dry-run"]) == 0
    after = {
        r["old_path"]
        for r in jn.load_registry(WB)
        if jn.is_junction(WB / (r.get("old_path") or "").replace("\\", "/"))
    }
    assert after == before
