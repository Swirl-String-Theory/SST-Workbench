#!/usr/bin/env python3
"""Independent KnotPlot before/after XYZ comparator with spatial strata.
No physical vortex-motion claim: KnotPlot relaxation is not Euler dynamics.
"""
import argparse,json,numpy as np
from pathlib import Path

def get_coords(path, expected=None):
    rows=[]
    for line in Path(path).read_text(encoding='utf-8',errors='replace').splitlines():
        parts=line.strip().split()
        if len(parts)==3:
            try:
                x=[float(q) for q in parts]
                if all(np.isfinite(x)):rows.append(x)
            except ValueError:pass
    p=np.asarray(rows,dtype=float)
    if p.ndim!=2 or p.shape[1]!=3:raise SystemExit(f'FAIL: cannot parse XYZ triples: {path}')
    if expected and len(p)!=expected:raise SystemExit(f'FAIL: {path} parsed {len(p)} points, expected {expected}')
    return p

def diagnostic(a,b):
    v=b-a
    d=np.linalg.norm(v,axis=1)
    dc=np.linalg.norm((b-b.mean(axis=0))-(a-a.mean(axis=0)),axis=1)
    ds=np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1)
    return {'n':len(a),'rms_displacement':float(np.sqrt(np.mean(d*d))),
       'max_displacement':float(d.max()),'rms_internal_after_remove_translation':float(np.sqrt(np.mean(dc*dc))),
       'rms_displacement_over_median_component_edge':float(np.sqrt(np.mean(d*d))/np.median(ds)),
       'centroid_shift':float(np.linalg.norm(b.mean(axis=0)-a.mean(axis=0)))}

def main():
    parser=argparse.ArgumentParser(description='Stratified KnotPlot go displacement and knot-vs-carrier diagnostics')
    parser.add_argument('before');parser.add_argument('after');parser.add_argument('--component-count',type=int,default=3)
    parser.add_argument('--region',choices=['SMOKE','ISOLATED'],default='SMOKE')
    args=parser.parse_args()
    sizes=[307]*3 if args.region=='SMOKE' else [300]
    if args.component_count!=len(sizes):raise SystemExit('Component count mismatch with declared reference')
    a=get_coords(args.before,sum(sizes));b=get_coords(args.after,sum(sizes))
    print(json.dumps({'total':diagnostic(a,b)},indent=2))
    start=0
    for i,n in enumerate(sizes):
        A=a[start:start+n];B=b[start:start+n]
        region={'whole_component': diagnostic(A,B)}
        if args.region=='SMOKE':
            # from v0.1.1 build: 139 carrier, 12 bridge, 144 local knot, 12 bridge
            region['carrier']=diagnostic(A[:139],B[:139])
            region['local_knot']=diagnostic(A[151:295],B[151:295])
            region['bridges']=diagnostic(np.r_[A[139:151],A[295:307]],np.r_[B[139:151],B[295:307]])
        print('COMPONENT',i, json.dumps(region,indent=2))
        start+=n
    if np.array_equal(a,b):print('WARNING: identical outputs; confirm go finished and iteration increased.')
    else:print('Coordinates changed; report regions above, do not infer Euler dynamics.')
if __name__=='__main__':main()
