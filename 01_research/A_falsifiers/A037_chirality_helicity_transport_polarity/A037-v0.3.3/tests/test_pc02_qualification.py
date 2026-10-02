"""PC02 tests for A037-v0.3.3."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pc02_selftest_cli():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "pc02_qualification.py")],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert json.loads(proc.stdout)["status"] == "PASS"


def test_split_never_physical_pass_when_unqualified():
    sys.path.insert(0, str(ROOT))
    import pc02_qualification as pc02

    labels = pc02.split_labels(mirror_pass=True, numerically_qualified=False)
    assert labels[pc02.LABEL_MIRROR] == "PASS"
    assert labels[pc02.LABEL_PHYSICAL] == "INVALID_NUMERICS"
    assert pc02.may_measure_chi_ij({"temporal": "FAIL", "spatial": "PASS", "mesh": "PASS"}) is False
