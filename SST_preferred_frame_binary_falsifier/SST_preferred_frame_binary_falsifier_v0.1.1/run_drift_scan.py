#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
import numpy as np
from pathlib import Path
from sst_pf_binary_falsifier.core import drift_scan, write_csv, write_json
from sst_pf_binary_falsifier.ideal_db import DEFAULT_IDEAL_KNOTS, DEFAULT_IDEAL_LINKS, load_knot_record, load_link_record, sample_record, audit_record

def floats(s: str): return [float(x) for x in s.split(',') if x.strip()]

def main() -> int:
    p=argparse.ArgumentParser(description='Galilean drift / knot-or-link sensitivity baseline scan.')
    p.add_argument('--n',type=int,default=72)
    p.add_argument('--points',help='Optional .npy or CSV x,y,z single centerline.')
    p.add_argument('--ideal-knot-id',help='Gilbert Ideal.txt id, e.g. 3:1:1.')
    p.add_argument('--ideal-link-id',help='Gilbert IdealLinks.txt id, e.g. L4a1. All STRING components are evolved.')
    p.add_argument('--ideal-knot-db',default=str(DEFAULT_IDEAL_KNOTS)); p.add_argument('--ideal-link-db',default=str(DEFAULT_IDEAL_LINKS))
    p.add_argument('--ideal-samples',type=int,default=96,help='Samples per Fourier component for dynamics.')
    p.add_argument('--ideal-scale-mode',choices=['native','sst_core'],default='sst_core',help='sst_core maps database D=1 to 2*r_c.')
    p.add_argument('--betas',default='0,0.0005,0.001,0.002,0.00364867628')
    p.add_argument('--steps',type=int,default=2); p.add_argument('--dt-factor',type=float,default=0.01)
    p.add_argument('--inject-chi0',type=float,default=0.0,help='Synthetic fit-recovery term; not SST physics.')
    p.add_argument('--inject-chi2',type=float,default=0.0,help='Synthetic fit-recovery term; not SST physics.')
    p.add_argument('--force-python',action='store_true'); p.add_argument('--out-dir',default='audit_out/drift')
    args=p.parse_args(); out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=True)
    chosen=sum(bool(x) for x in [args.points,args.ideal_knot_id,args.ideal_link_id])
    if chosen>1: p.error('Choose at most one of --points, --ideal-knot-id, --ideal-link-id')
    pts=None; geom_meta=None
    if args.points:
        pp=Path(args.points)
        if pp.suffix.lower()=='.npy': pts=np.load(pp)
        else: pts=np.loadtxt(pp,delimiter=',',skiprows=1 if pp.read_text(encoding='utf-8').splitlines()[0].lower().startswith('x') else 0)
    elif args.ideal_knot_id:
        rec=load_knot_record(args.ideal_knot_id,args.ideal_knot_db); pts=sample_record(rec,args.ideal_samples,scale_mode=args.ideal_scale_mode)
        geom_meta={'source_validation':audit_record(rec,samples=None,scale_mode=args.ideal_scale_mode,linking=False),
                   'dynamics_discretization':audit_record(rec,samples=args.ideal_samples,scale_mode=args.ideal_scale_mode,linking=False)}
    elif args.ideal_link_id:
        rec=load_link_record(args.ideal_link_id,args.ideal_link_db); pts=sample_record(rec,args.ideal_samples,scale_mode=args.ideal_scale_mode)
        geom_meta={'source_validation':audit_record(rec,samples=None,scale_mode=args.ideal_scale_mode,linking=True),
                   'dynamics_discretization':audit_record(rec,samples=args.ideal_samples,scale_mode=args.ideal_scale_mode,linking=True)}
    res=drift_scan(n=args.n,points=pts,beta_values=floats(args.betas),steps=args.steps,dt_factor=args.dt_factor,
                   force_python=args.force_python,inject_chi0=args.inject_chi0,inject_chi2=args.inject_chi2)
    if geom_meta is not None:
        res['ideal_geometry']=geom_meta
        src=geom_meta['source_validation']; res['geometry_source']=f"Gilbert_{src['kind']}:{src['id']}"
    write_json(out/'drift_scan.json',res); write_csv(out/'drift_scan.csv',res['rows'])
    print(json.dumps({k:v for k,v in res.items() if k!='rows'},indent=2))
    return 0 if res['baseline_ok'] else 1
if __name__=='__main__': raise SystemExit(main())
