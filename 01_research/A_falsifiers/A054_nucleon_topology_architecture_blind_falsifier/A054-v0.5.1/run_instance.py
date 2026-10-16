from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
from framework_bootstrap import load_framework
FRAMEWORK_ROOT=load_framework()
from sst_falsifier.runner import run_mode
if __name__=="__main__":
    mode=sys.argv[1] if len(sys.argv)>1 else "BASIC"
    raise SystemExit(run_mode(ROOT,mode))
