#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math
from sst_counterpulley.core import DEFAULT_DATA,prepare_centerline,write_csv,write_json
from sst_counterpulley.orbit import search_relative_periodic_orbit,scan_rpo_seeds

def main()->int:
    ap=argparse.ArgumentParser(description="Alpha-blind relative-periodic-orbit search.")
    ap.add_argument("--data",default=str(DEFAULT_DATA)); ap.add_argument("--n",type=int,default=64)
    ap.add_argument("--out-dir",default="rpo_out"); ap.add_argument("--scan",action="store_true")
    ap.add_argument("--force-python",action="store_true")
    a=ap.parse_args(); c,m=prepare_centerline(data_path=a.data,n=a.n); D=float(m["D_metadata"])
    if a.scan:
        rows=scan_rpo_seeds(c,D=D,force_python=a.force_python); write_csv(f"{a.out_dir}/rpo_seed_scan.csv",rows); print(json.dumps(rows[:10],indent=2))
    else:
        r=search_relative_periodic_orbit(c,D=D,force_python=a.force_python,return_trajectory=False)
        clean={"candidate":r["candidate"],"recurrence_trace":r["recurrence_trace"]}; write_json(f"{a.out_dir}/rpo_search.json",clean); print(json.dumps(clean,indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())
