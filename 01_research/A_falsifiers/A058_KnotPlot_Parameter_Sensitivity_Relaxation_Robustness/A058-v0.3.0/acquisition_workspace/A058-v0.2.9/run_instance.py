from __future__ import annotations
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
from framework_bootstrap import load_framework
load_framework()
from sst_falsifier.runner import run_mode

def main():
    mode=sys.argv[1].upper() if len(sys.argv)>1 else "BASIC"
    return run_mode(ROOT,mode)
if __name__=="__main__":
    raise SystemExit(main())
