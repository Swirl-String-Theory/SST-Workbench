"""PC03 tests for A034-v0.2.3."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pc03_selftest_cli():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "pc03_dual_branch.py")],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert json.loads(proc.stdout)["status"] == "PASS"


def test_weak_manifold_label():
    sys.path.insert(0, str(ROOT))
    import pc03_dual_branch as pc03

    assert (
        pc03.classify_energetic(
            f_proj=0.002, gradient_norm=0.0, hessian_min_eig=1.0, numerically_ok=True
        )
        == "REDUCED_MANIFOLD_BREAKDOWN"
    )
