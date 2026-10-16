from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent

from framework_bootstrap import load_framework

FRAMEWORK_ROOT = load_framework()
from sst_falsifier import __version__ as _actual_framework_version
if FRAMEWORK_ROOT.name != "SST_Falsifier_Framework_v1.0.7" or _actual_framework_version != "1.0.7":
    raise RuntimeError(f"A061 strict framework pin violation: {FRAMEWORK_ROOT} version {_actual_framework_version}")
from sst_falsifier.runner import run_mode

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "BASIC"
    raise SystemExit(run_mode(ROOT, mode))
