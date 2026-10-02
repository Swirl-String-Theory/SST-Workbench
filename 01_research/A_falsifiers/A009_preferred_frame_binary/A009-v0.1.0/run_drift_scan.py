#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
import numpy as np
from pathlib import Path
from sst_pf_binary_falsifier.core import drift_scan, write_csv, write_json


def floats(s: str): return [float(x) for x in s.split(',') if x.strip()]

def main() -> int:
    p=argparse.ArgumentParser(description='Galilean drift / knot sensitivity baseline scan.')
    p.add_argument('--n',type=int,default=72)
    p.add_argument('--points',help='Optional .npy or CSV x,y,z centerline; overrides generated T(2,3) seed.')
    p.add_argument('--betas',default='0,0.0005,0.001,0.002,0.00364867628')
    p.add_argument('--steps',type=int,default=2)
    p.add_argument('--dt-factor',type=float,default=0.01)
    p.add_argument('--inject-chi0',type=float,default=0.0,help='Synthetic fit-recovery term; not SST physics.')
    p.add_argument('--inject-chi2',type=float,default=0.0,help='Synthetic fit-recovery term; not SST physics.')
    p.add_argument('--force-python',action='store_true')
    p.add_argument('--out-dir',default='audit_out/drift')
    args=p.parse_args()
    out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=True)
    pts=None
    if args.points:
        pp=Path(args.points)
        if pp.suffix.lower()=='.npy': pts=np.load(pp)
        else: pts=np.loadtxt(pp,delimiter=',',skiprows=1 if pp.read_text(encoding='utf-8').splitlines()[0].lower().startswith('x') else 0)
    res=drift_scan(n=args.n,points=pts,beta_values=floats(args.betas),steps=args.steps,dt_factor=args.dt_factor,
                   force_python=args.force_python,inject_chi0=args.inject_chi0,inject_chi2=args.inject_chi2)
    write_json(out/'drift_scan.json',res); write_csv(out/'drift_scan.csv',res['rows'])
    print(json.dumps({k:v for k,v in res.items() if k!='rows'},indent=2))
    return 0 if res['baseline_ok'] else 1
if __name__=='__main__': raise SystemExit(main())
