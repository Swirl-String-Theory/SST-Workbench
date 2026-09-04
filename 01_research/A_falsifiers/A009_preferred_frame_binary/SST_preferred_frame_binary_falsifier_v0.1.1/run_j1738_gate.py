#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from sst_pf_binary_falsifier.core import j1738_corrected_pdot, write_json

def main() -> int:
    p=argparse.ArgumentParser(description='PSR J1738+0333 corrected orbital-decay gate.')
    p.add_argument('--model-pdot-corr',type=float,help='SST prediction in s/s. Omit for data-only correction.')
    p.add_argument('--out',default='audit_out/j1738_gate.json')
    a=p.parse_args(); r=j1738_corrected_pdot(a.model_pdot_corr); write_json(a.out,r); print(json.dumps(r,indent=2))
    return 1 if r['status'].startswith('FALSIFIED') else 0
if __name__=='__main__': raise SystemExit(main())
