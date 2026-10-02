"""Tests for paper_upgrade_numerics ladders."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
SCRIPT = WB / "07_scripts" / "paper_upgrade_numerics.py"

sys.path.insert(0, str(WB / "07_scripts"))
import paper_upgrade_numerics as pun  # noqa: E402


def test_selftest_cli():
    proc = subprocess.run([sys.executable, str(SCRIPT), "selftest"], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["status"] == "PASS"


def test_temporal_spatial_mesh_helpers():
    assert pun.temporal_ladder_pass([(1.0, 1.0), (0.5, 1.01), (0.25, 1.011)])["status"] == "PASS"
    assert pun.spatial_ladder_pass([(16, 1.0), (32, 1.01), (64, 1.011)])["status"] == "PASS"
    assert pun.mesh_quality_pass(ds_cv=0.1, n_points=72)["status"] == "PASS"
