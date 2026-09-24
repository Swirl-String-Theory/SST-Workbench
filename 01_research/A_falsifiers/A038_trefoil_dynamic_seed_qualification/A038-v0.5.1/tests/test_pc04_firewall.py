"""PC04 tests for A038-v0.5.1."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pc04_selftest_cli():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "pc04_firewall.py"), "--selftest"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert json.loads(proc.stdout)["status"] == "PASS"


def test_never_fail_trefoil_on_selftest():
    sys.path.insert(0, str(ROOT))
    import pc04_firewall as pc04

    r = pc04.preflight(
        {
            "A034": pc04._mk("A034", "SST-ADMISSIBILITY-1.0", kind="SELFTEST", synthetic=True),
            "A037": pc04._mk("A037", "SST-SYMMETRY-SELECTION-1.0", kind="SELFTEST", synthetic=True),
        }
    )
    assert r["fail_trefoil"] is False
    assert r["primary_block"] == "BLOCKED_UPSTREAM_SELFTEST"
