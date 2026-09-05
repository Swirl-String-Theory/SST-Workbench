
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).parents[1]

def test_qm_wrapper_exposes_native_build_controls():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_qm.py"), "--help"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    assert "--skip-native-build" in result.stdout
    assert "--force-native-build" in result.stdout
    assert "--build-verbose" in result.stdout

def test_native_preflight_help():
    result = subprocess.run(
        [sys.executable, str(ROOT / "run_native_preflight.py"), "--help"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    assert "--force" in result.stdout
