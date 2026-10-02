"""C006-v0.2.2 cert provenance tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pc_cert_provenance_cli():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "pc_cert_provenance.py")],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert json.loads(proc.stdout)["status"] == "PASS"
    assert json.loads(proc.stdout)["promotion_allowed"] is False
