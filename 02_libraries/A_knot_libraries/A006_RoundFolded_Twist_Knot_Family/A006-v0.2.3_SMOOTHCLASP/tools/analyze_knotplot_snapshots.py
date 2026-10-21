"""POST-KnotPlot-only analysis. Does not infer physical Euler dynamics.
Usage: python tools/analyze_knotplot_snapshots.py 5_2 SOFT 512
Requires three snapshots written after completed relaxation steps.
"""
from pathlib import Path
import sys,argparse,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from build import topology
from clearance import global_min_nonlocal
from near_unknot import approximate_curvature

def summarize(before,after):
    d=after-before
    shift=d.mean(axis=0)
    return {'RMS_displacement':float(np.sqrt(np.mean(np.sum(d*d,axis=1)))),
            'max_displacement':float(np.max(np.linalg.norm(d,axis=1))),
            'centroid_shift':float(np.linalg.norm(shift)),
            'RMS_after_remove_translation':float(np.sqrt(np.mean(np.sum((d-shift)**2,axis=1))))}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('label',choices=['5_2','6_1']);parser.add_argument('profile',choices=['SOFT','BALANCED','TIGHT']);parser.add_argument('n',type=int)
    a=parser.parse_args()
    name=f'SmoothClasp_{a.label}_{a.profile}_N{a.n:04}'
    d=ROOT/'output'/'individual'/name
    paths=[d/f'{name}_{s}.xyz' for s in ['BEFORE','AFTER1','AFTER33']]
    arrays=[];checks=[]
    for path in paths:
        if not path.exists():raise SystemExit('Missing snapshot: '+str(path)+' (save it after KnotPlot actually finishes each go)')
        x=np.loadtxt(path)
        if x.shape!=(a.n,3) or not np.isfinite(x).all():raise SystemExit('Snapshot incompatible shape or non-finite numbers: '+str(path))
        try: top=topology(x,a.label);status='PASS'
        except Exception as exc: top={'error':str(exc)};status='UNRESOLVED_OR_FAIL'
        checks.append({'snapshot':path.name,'topology':top,'topology_status':status,
             'min_clearance':global_min_nonlocal(x)['distance'],
             'max_polygonal_curvature':float(np.max(approximate_curvature(x)))})
        arrays.append(x)
    report={'analysis':'KnotPlot geometric diagnostic only','label':a.label,'profile':a.profile,'n':a.n,
       'intervals':{'0_to_1':summarize(arrays[0],arrays[1]),'1_to_33':summarize(arrays[1],arrays[2])},
       'snapshots':checks,'warning':'No guarantee of topology preservation BETWEEN checkpoints; independent proof required.'}
    target=d/f'{name}_KNOTPLOT_ANALYSIS.json'
    target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2));print('Wrote',target)
if __name__=='__main__':main()
