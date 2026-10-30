"""Pre-run A075-v0.2.9 byte-exact source resolver inspection; no mutations."""
from __future__ import annotations
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from framework_bootstrap import load_framework
load_framework()
from experiment.qualification import inspect_sources
if __name__=='__main__':
    result=inspect_sources(ROOT)
    print(json.dumps(result,indent=2,ensure_ascii=False))
    raise SystemExit(0 if result['passed'] else 2)
