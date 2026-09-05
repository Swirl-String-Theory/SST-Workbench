#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from fermat_ext.core import write_json
from fermat_ext.multistart import multistart_closed_orbit_search, selected_seed_convergence

def main()->int:
 p=argparse.ArgumentParser(description='v0.6.0 multistart selection followed by two-axis convergence.')
 p.add_argument('--knots',nargs='+',default=['0_1','3_1','4_1','5_2']); p.add_argument('--epsilon',type=float,default=.0019)
 p.add_argument('--selection-centerline-points',type=int,default=8192); p.add_argument('--centerline-point-counts',nargs='+',type=int,default=[8192,16384,32768]); p.add_argument('--step-counts',nargs='+',type=int,default=[256,512,1024])
 p.add_argument('--stations',type=int,default=4); p.add_argument('--angles',type=int,default=8); p.add_argument('--period-multipliers',nargs='+',type=float,default=[.5,1,2,4]); p.add_argument('--max-iterations',type=int,default=12)
 p.add_argument('--force-python',action='store_true'); p.add_argument('--no-auto-build',action='store_true'); p.add_argument('--require-native',action='store_true'); p.add_argument('--out-dir',default='v0.6.0_convergence_output')
 a=p.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True); results={}; rows=[]
 for i,k in enumerate(a.knots):
  sel=multistart_closed_orbit_search(k,epsilon=a.epsilon,centerline_points=a.selection_centerline_points,stations=a.stations,angles=a.angles,period_multipliers=a.period_multipliers,coarse_step_count=128,coarse_iterations=2,refine_top_k=8,refine_step_count=512,refine_iterations=a.max_iterations,force_python=a.force_python,auto_build=(not a.no_auto_build) if i==0 else False)
  if not sel.get('best'):
   conv=None
  else:
   conv=selected_seed_convergence(k,sel['best']['identity'],epsilon=a.epsilon,centerline_point_counts=a.centerline_point_counts,step_counts=a.step_counts,stations=a.stations,angles=a.angles,max_iterations=a.max_iterations,force_python=a.force_python,auto_build=False)
  if a.require_native:
   backend=(sel.get('best') or {}).get('shot',{}).get('best',{}).get('integration',{}).get('backend',{}).get('backend')
   if backend!='cpp': raise SystemExit('native backend required')
  result={'selection':sel,'convergence':conv}; results[k]=result; write_json(out/f'{k}.json',result)
  rows.append({'knot_id':k,'best_score':(sel.get('best') or {}).get('score'),'global_closed_orbit_certified':bool(conv and conv['global_closed_orbit_certified'])})
 combined={'schema':'sst.fermat.v0.6.0-selected-convergence-matrix','rows':rows,'results':results,'any_global_closed_orbit_certified':any(r['global_closed_orbit_certified'] for r in rows),'qsm_certified':False}; write_json(out/'selected_convergence.json',combined); print(json.dumps(rows,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
