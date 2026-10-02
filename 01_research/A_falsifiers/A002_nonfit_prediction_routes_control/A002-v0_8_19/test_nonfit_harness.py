from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def run(*args: str):
    return subprocess.run([sys.executable, str(ROOT / "nonfit_harness.py"), *args], cwd=ROOT, text=True, capture_output=True)


def test_default_report_has_four_gates():
    out = ROOT / "out" / "test_default.json"
    res = run("--out-json", str(out), "--out-csv", str(ROOT / "out" / "test_default.csv"))
    assert res.returncode in (0, 2), res.stderr + res.stdout
    data = json.loads(out.read_text())
    assert len(data["gates"]) == 4
    assert "ii_non_fitted_prediction_protocol" in data["gates"]
    assert data["gates"]["ii_non_fitted_prediction_protocol"]["status"] == "DERIVED"


def test_negative_control_target_mass_as_input_fails():
    out = ROOT / "out" / "test_negative.json"
    res = run("--use-target-mass-as-input", "--out-json", str(out), "--out-csv", str(ROOT / "out" / "test_negative.csv"))
    assert res.returncode == 2
    data = json.loads(out.read_text())
    assert data["gates"]["ii_non_fitted_prediction_protocol"]["status"] == "FAILED"


if __name__ == "__main__":
    test_default_report_has_four_gates()
    test_negative_control_target_mass_as_input_fails()
    print("PASS")
