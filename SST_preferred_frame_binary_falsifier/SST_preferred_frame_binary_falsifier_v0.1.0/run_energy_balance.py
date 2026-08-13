#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json
import numpy as np
from sst_pf_binary_falsifier.core import energy_balance_gate, write_json

def main() -> int:
    p=argparse.ArgumentParser(description='Compare orbital dE/dt, far-field flux and radiation-reaction power.')
    p.add_argument('--csv',help='Columns: t_s,E_orbit_J,flux_inf_W,p_rr_W. If omitted, run manufactured closure data.')
    p.add_argument('--rel-tolerance',type=float,default=0.05)
    p.add_argument('--out',default='audit_out/energy_balance_gate.json')
    a=p.parse_args()
    if a.csv:
        rows=list(csv.DictReader(open(a.csv,newline='',encoding='utf-8')))
        t=[float(r['t_s']) for r in rows]; E=[float(r['E_orbit_J']) for r in rows]
        F=[float(r['flux_inf_W']) for r in rows]; P=[float(r['p_rr_W']) for r in rows]
    else:
        t=np.linspace(0,10,101); power=2.5; E=100-power*t; F=np.full_like(t,power); P=np.full_like(t,-power)
    r=energy_balance_gate(t,E,F,P,a.rel_tolerance); write_json(a.out,r); print(json.dumps(r,indent=2)); return 0 if r['ok'] else 1
if __name__=='__main__': raise SystemExit(main())
