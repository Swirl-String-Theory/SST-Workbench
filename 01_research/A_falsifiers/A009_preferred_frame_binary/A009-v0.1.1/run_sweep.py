#!/usr/bin/env python3
"""Sweep beta drift magnitudes, following the standard SST cpp_pybind template pattern."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from sst_pf_binary_falsifier.core import drift_scan,write_csv,write_json

def vals(s): return [float(x.strip()) for x in s.split(',') if x.strip()]

def main()->int:
    p=argparse.ArgumentParser(description='Sweep SST preferred-frame drift magnitudes.')
    p.add_argument('--betas',default='0,0.0005,0.001,0.002,0.00364867628')
    p.add_argument('--n',type=int,default=64); p.add_argument('--steps',type=int,default=1)
    p.add_argument('--force-python',action='store_true'); p.add_argument('--force-build',action='store_true')
    p.add_argument('--out-json',default='audit_out/sweep.json'); p.add_argument('--out-csv',default='audit_out/sweep.csv')
    a=p.parse_args()
    if a.force_build:
        from sst_pf_binary_falsifier.build_ext_if_needed import build_if_needed
        build_if_needed(force=True,verbose=True)
    r=drift_scan(n=a.n,beta_values=vals(a.betas),steps=a.steps,force_python=a.force_python)
    write_json(a.out_json,r); write_csv(a.out_csv,r['rows'])
    print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2)); return 0 if r['baseline_ok'] else 1
if __name__=='__main__': raise SystemExit(main())
