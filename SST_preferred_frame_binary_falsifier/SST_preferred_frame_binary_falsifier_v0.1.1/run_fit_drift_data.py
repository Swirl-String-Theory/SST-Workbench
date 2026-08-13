#!/usr/bin/env python3
"""Fit chi0/chi2 to externally generated SST drift-energy data."""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
from sst_pf_binary_falsifier.core import fit_drift_sensitivity,write_json

def main()->int:
    p=argparse.ArgumentParser(description='Fit SST drift sensitivity from external solver data.')
    p.add_argument('--csv',required=True,help='Columns: beta,mu,energy_J. mu=cos(angle between W and chosen object axis).')
    p.add_argument('--e0',type=float,help='Reference energy. Default: mean energy of beta=0 rows.')
    p.add_argument('--chi0-max',type=float,help='Optional absolute acceptance threshold for chi0.')
    p.add_argument('--chi2-max',type=float,help='Optional absolute acceptance threshold for chi2.')
    p.add_argument('--out',default='audit_out/external_drift_fit.json')
    a=p.parse_args(); raw=list(csv.DictReader(open(a.csv,newline='',encoding='utf-8')))
    parsed=[]
    for r in raw:
        beta=float(r['beta']); mu=float(r['mu']); energy=float(r['energy_J'])
        parsed.append((beta,mu,energy))
    if not parsed: raise SystemExit('empty CSV')
    e0=a.e0
    if e0 is None:
        zeros=[e for b,m,e in parsed if abs(b)<1e-30]
        if not zeros: raise SystemExit('Need at least one beta=0 row or --e0')
        e0=sum(zeros)/len(zeros)
    rows=[]
    for beta,mu,e in parsed:
        b2=beta*beta
        rows.append({'beta2':b2,'axis_projection_sq':b2*mu*mu,'delta_E_over_E0':(e-e0)/e0})
    fit=fit_drift_sensitivity(rows)
    gates={}
    if a.chi0_max is not None: gates['chi0']=abs(fit['chi0'])<=a.chi0_max
    if a.chi2_max is not None: gates['chi2']=abs(fit['chi2'])<=a.chi2_max
    out={'source_csv':a.csv,'E0_J':e0,'fit':fit,'gates':gates,
         'status':'PASS_THRESHOLDS' if gates and all(gates.values()) else ('FAIL_THRESHOLDS' if gates else 'FIT_ONLY_NO_THRESHOLDS'),
         'warning':'chi thresholds are user-supplied. Observational alpha1/alpha2 bounds cannot be applied until an SST->PPN mapping is derived.'}
    write_json(a.out,out); print(json.dumps(out,indent=2)); return 1 if out['status']=='FAIL_THRESHOLDS' else 0
if __name__=='__main__': raise SystemExit(main())
