from __future__ import annotations
from pathlib import Path
import runpy,sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from framework_bootstrap import load_framework
load_framework()
if len(sys.argv)<2:
    raise SystemExit("Usage: run_python.py <script.py|-m module> [args...]")
if sys.argv[1]=="-m":
    mod=sys.argv[2]; sys.argv=sys.argv[2:]; runpy.run_module(mod,run_name="__main__",alter_sys=True)
else:
    script=Path(sys.argv[1]); script=script if script.is_absolute() else ROOT/script
    sys.argv=[str(script),*sys.argv[2:]]; runpy.run_path(str(script),run_name="__main__")
