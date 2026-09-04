#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from datetime import datetime
from pathlib import Path
from sst6.campaign import load_config, run_campaign
from sst6.io import write_json

ROOT=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser(description="Run BASIC then EXTENDED SST six-source blind campaigns into one session folder.")
    ap.add_argument("--dataset",required=True)
    ap.add_argument("--out-dir",default="")
    ap.add_argument("--force-python",action="store_true")
    ap.add_argument("--require-native",action="store_true")
    args=ap.parse_args()
    d=Path(args.dataset); d=d if d.is_absolute() else (ROOT/d).resolve()
    out=(Path(args.out_dir) if args.out_dir else ROOT/"outputs"/f"run_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    if not out.is_absolute(): out=ROOT/out
    out.mkdir(parents=True,exist_ok=True)
    basic=run_campaign(load_config(ROOT/'config/campaign_basic.json'),d,out/'basic',force_python=args.force_python,require_native=args.require_native)
    extended=run_campaign(load_config(ROOT/'config/campaign_extended.json'),d,out/'extended',force_python=args.force_python,require_native=args.require_native)
    summary={"dataset":str(d),"out_dir":str(out),"basic":basic,"extended":extended,"pipeline_ok":bool(basic.get('pipeline_ok') and extended.get('pipeline_ok')),
             "interpretation":"Research-hypothesis FAILs are retained as scientific outcomes; pipeline_ok only reflects execution/calibration/identity integrity."}
    write_json(out/'RUN_ALL_SUMMARY.json',summary)
    print(json.dumps(summary,indent=2))
    print(f"[SST6] run_all outputs: {out}")
    return 0 if summary['pipeline_ok'] else 2
if __name__=='__main__': raise SystemExit(main())
