#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, platform, sys
from pathlib import Path
import numpy as np
from sst6.constants import CANONICAL_CONSTANTS
from sst6.io import discover_datasets
from native_ext import load_backend

ROOT=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--dataset",required=True); ap.add_argument("--require-native",action="store_true"); args=ap.parse_args()
    d=Path(args.dataset); d=d if d.is_absolute() else (ROOT/d).resolve()
    items=discover_datasets(d)
    backend,bname=load_backend(force_python=False,force_build=False,build_verbose=False)
    info={"python":sys.version,"platform":platform.platform(),"numpy":np.__version__,"dataset":str(d),"dataset_count":len(items),"backend":bname,"canonical_constants":CANONICAL_CONSTANTS}
    print(json.dumps(info,indent=2))
    if not items: return 3
    if args.require_native and bname!="cpp": return 4
    return 0
if __name__=="__main__": raise SystemExit(main())
