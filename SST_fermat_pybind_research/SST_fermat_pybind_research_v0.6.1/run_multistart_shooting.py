#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from fermat_ext.core import write_json
from fermat_ext.multistart import multistart_closed_orbit_search

def main()->int:
 p=argparse.ArgumentParser(description='v0.6.1 finite multistart closed-orbit search.')
 p.add_argument('--knots',nargs='+',default=['0_1','3_1','4_1','5_2']); p.add_argument('--epsilon',type=float,default=.0019)
 p.add_argument('--centerline-points',type=int,default=8192); p.add_argument('--stations',type=int,default=4); p.add_argument('--angles',type=int,default=8)
 p.add_argument('--period-multipliers',nargs='+',type=float,default=[.5,1,2,4]); p.add_argument('--coarse-steps',type=int,default=128); p.add_argument('--coarse-iterations',type=int,default=2)
 p.add_argument('--refine-top-k',type=int,default=8); p.add_argument('--refine-steps',type=int,default=512); p.add_argument('--refine-iterations',type=int,default=12)
 p.add_argument('--force-python',action='store_true'); p.add_argument('--no-auto-build',action='store_true'); p.add_argument('--require-native',action='store_true'); p.add_argument('--out-dir',default='v0.6.1_multistart_output')
 a=p.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True); results={}; rows=[]
 for i,k in enumerate(a.knots):
  r=multistart_closed_orbit_search(k,epsilon=a.epsilon,centerline_points=a.centerline_points,stations=a.stations,angles=a.angles,period_multipliers=a.period_multipliers,coarse_step_count=a.coarse_steps,coarse_iterations=a.coarse_iterations,refine_top_k=a.refine_top_k,refine_step_count=a.refine_steps,refine_iterations=a.refine_iterations,force_python=a.force_python,auto_build=(not a.no_auto_build) if i==0 else False)
  if a.require_native:
   backend=(r.get('best') or {}).get('shot',{}).get('best',{}).get('integration',{}).get('backend',{}).get('backend')
   if backend!='cpp': raise SystemExit('native backend required')
  results[k]=r; write_json(out/f'{k}.json',r)
  rows.append({'knot_id':k,'seed_count':r['seed_count'],'status':r['status'],'best_score':(r.get('best') or {}).get('score'),'resolved':r['resolved_closed_orbit_found']})
 combined={'schema':'sst.fermat.multistart-matrix.v0.6.1','rows':rows,'results':results,'any_resolved':any(x['resolved'] for x in rows),'global_closed_orbit_certified':False,'qsm_certified':False}; write_json(out/'multistart.json',combined); print(json.dumps(rows,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
