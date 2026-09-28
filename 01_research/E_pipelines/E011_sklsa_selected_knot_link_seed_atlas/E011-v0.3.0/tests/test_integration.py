from pathlib import Path
import json, subprocess, sys

HERE = Path(__file__).resolve().parents[1]


def test_poc_runner_classifies_missing_as_operational_error(synthetic_workbench, tmp_path):
    out = tmp_path / "e011-out"
    cmd = [sys.executable, str(HERE / "tools" / "run_analysis.py"), "--workbench-root", str(synthetic_workbench), "--mode", "poc", "--output-root", str(out)]
    cp = subprocess.run(cmd, capture_output=True, text=True)
    assert cp.returncode == 2
    summary = json.loads((out / "RUN_SUMMARY.json").read_text())
    assert summary["execution_gate"] == "FAIL_CLOSED"
    assert summary["operational_error_count"] > 0
