"""PC01 regression tests for D006-v0.4.1."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "pc01_regressions.py"


def test_pc01_module_import():
    sys.path.insert(0, str(ROOT))
    import pc01_regressions as reg  # noqa: F401

    out = reg.run_all()
    assert out["status"] == "PASS"
    assert out["promotion_allowed_any"] is False


def test_pc01_cli():
    proc = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, cwd=str(ROOT))
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["status"] == "PASS"
    assert set(payload["cases"]) == {"test_a", "test_b", "test_c"}
