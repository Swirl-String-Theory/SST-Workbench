#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from sst_pf_binary_falsifier.core import preferred_frame_gate, write_json

def main() -> int:
    p=argparse.ArgumentParser(description='Preferred-frame observational gate. No SST->PPN mapping is assumed.')
    p.add_argument('--alpha1-eff',type=float)
    p.add_argument('--alpha2-eff',type=float)
    p.add_argument('--out',default='audit_out/preferred_frame_gate.json')
    a=p.parse_args(); r=preferred_frame_gate(a.alpha1_eff,a.alpha2_eff); write_json(a.out,r); print(json.dumps(r,indent=2))
    return 1 if r['status']=='FAIL_AVAILABLE_GATES' else 0
if __name__=='__main__': raise SystemExit(main())
