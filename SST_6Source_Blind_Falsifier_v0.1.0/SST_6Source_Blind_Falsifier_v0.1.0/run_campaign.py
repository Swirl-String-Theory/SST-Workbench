#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from datetime import datetime
from pathlib import Path
from sst6.campaign import load_config, run_campaign

ROOT=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser(description="Run the SST six-source blind falsifier campaign.")
    ap.add_argument("--config",required=True)
    ap.add_argument("--dataset",required=True)
    ap.add_argument("--out-dir",default="")
    ap.add_argument("--force-python",action="store_true")
    ap.add_argument("--require-native",action="store_true")
    args=ap.parse_args()
    cfgp=Path(args.config); cfgp=cfgp if cfgp.is_absolute() else ROOT/cfgp
    d=Path(args.dataset); d=d if d.is_absolute() else (ROOT/d).resolve()
    if args.out_dir:
        out=Path(args.out_dir); out=out if out.is_absolute() else ROOT/out
    else:
        stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
        out=ROOT/"outputs"/f"{cfgp.stem}_{stamp}"
    summary=run_campaign(load_config(cfgp),d,out,force_python=args.force_python,require_native=args.require_native)
    print(json.dumps(summary,indent=2))
    print(f"[SST6] outputs: {out}")
    return 0 if summary.get("pipeline_ok",False) else 2

if __name__=="__main__": raise SystemExit(main())
