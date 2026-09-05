#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,datetime,sys
from pathlib import Path
from kj_sst.blind import prepare
from kj_sst.campaign import run_campaign,unblind
from native_ext.core import run_smoke

def main():
    p=argparse.ArgumentParser(description="Kelvin-Joule SST blind transient-energy campaign")
    p.add_argument("--dataset",default=r"..\..\KnotPlot\knots\final")
    p.add_argument("--profile",choices=["basic","extended"],default="basic")
    p.add_argument("--backend",choices=["auto","sycl","openmp","python"],default="auto")
    p.add_argument("--allow-sycl-cpu",action="store_true")
    p.add_argument("--out",default="")
    args=p.parse_args()
    cfg=json.loads((Path(__file__).resolve().parent/"configs"/f"{args.profile}.json").read_text())
    probe=run_smoke(args.backend,args.allow_sycl_cpu,False)
    chosen=str(probe.get("backend","python"))
    if args.profile=="extended" and chosen=="python" and args.backend!="python":
        print("[KJ-SST] REFUSING extended campaign on accidental Python fallback. Install/build SYCL or OpenMP, or explicitly pass --backend python.",file=sys.stderr)
        return 3
    if chosen=="python":
        print("[KJ-SST] WARNING: Python backend selected; intended only for smoke/small campaigns.",file=sys.stderr)
    stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S");out=Path(args.out) if args.out else Path("outputs")/f"{args.profile}_{stamp}"
    print(f"[KJ-SST] profile={args.profile} dataset={args.dataset} requested_backend={args.backend} chosen_backend={chosen}")
    prepare(args.dataset,out,cfg)
    run_campaign(out,args.backend,args.allow_sycl_cpu)
    summary=unblind(out)
    print(json.dumps({"output":str(out.resolve()),"chosen_backend":chosen,**summary},indent=2))
    return 0 if summary["failed_energy_rows"]==0 else 2
if __name__=="__main__":raise SystemExit(main())
