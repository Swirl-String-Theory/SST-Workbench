#!/usr/bin/env python3
"""Single compact audit, matching the standard SST cpp_pybind template entry-point pattern."""
from __future__ import annotations
import argparse,json
from sst_pf_binary_falsifier.core import drift_scan,write_json

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--force-python',action='store_true'); p.add_argument('--force-build',action='store_true')
    p.add_argument('--out',default='example_result.json'); a=p.parse_args()
    if a.force_build:
        from sst_pf_binary_falsifier.build_ext_if_needed import build_if_needed
        build_if_needed(force=True,verbose=True)
    r=drift_scan(n=48,beta_values=(0,0.001,0.00364867628),steps=1,force_python=a.force_python)
    write_json(a.out,r); print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2)); return 0 if r['baseline_ok'] else 1
if __name__=='__main__': raise SystemExit(main())
