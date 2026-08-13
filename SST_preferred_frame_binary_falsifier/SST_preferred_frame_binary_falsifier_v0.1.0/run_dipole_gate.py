#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from sst_pf_binary_falsifier.core import dipole_universality_gate, write_json

def main() -> int:
    p=argparse.ArgumentParser(description='Test universality of SST radiative/gravitational q/m and dipole mismatch.')
    p.add_argument('--objects',help='JSON file: list of {name,mass,charge}. Default runs a universal manufactured case.')
    p.add_argument('--tolerance',type=float,default=1e-10)
    p.add_argument('--out',default='audit_out/dipole_gate.json')
    a=p.parse_args()
    if a.objects:
        objects=json.loads(Path(a.objects).read_text(encoding='utf-8'))
    else:
        objects=[{'name':'A','mass':1.0,'charge':2.0},{'name':'B','mass':3.0,'charge':6.0}]
    r=dipole_universality_gate(objects,a.tolerance); write_json(a.out,r); print(json.dumps(r,indent=2))
    return 0 if r['universal_within_tolerance'] else 2
if __name__=='__main__': raise SystemExit(main())
