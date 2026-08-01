#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from fermat_ext.certification import scan_stationary_candidates
from fermat_ext.core import write_json
from fermat_ext.geodesic import shoot_closed_orbit
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS, sample_ideal_knot

def main() -> int:
    p=argparse.ArgumentParser(description='Shoot full 3-D Fermat rays from resolved local-minimum seeds.')
    p.add_argument('--knots',nargs='+',default=list(DEFAULT_KNOT_IDS)); p.add_argument('--epsilon',type=float,default=0.0019)
    p.add_argument('--centerline-points',type=int,default=4096); p.add_argument('--station',type=int,default=0); p.add_argument('--angle-index',type=int,default=0)
    p.add_argument('--candidate-angles',type=int,default=8); p.add_argument('--steps',type=int,default=512); p.add_argument('--max-iterations',type=int,default=10)
    p.add_argument('--position-tol',type=float,default=1e-7); p.add_argument('--direction-tol',type=float,default=1e-7)
    p.add_argument('--force-python',action='store_true'); p.add_argument('--no-auto-build',action='store_true'); p.add_argument('--require-native',action='store_true')
    p.add_argument('--out-dir',default='geodesic_shooting')
    a=p.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    results={}; rows=[]
    for i,k in enumerate(a.knots):
        atlas=scan_stationary_candidates(k,epsilon=a.epsilon,centerline_points=a.centerline_points,stations=max(1,a.station+1),angles=a.candidate_angles,
            rho_min=0.0005,rho_max=0.01,bracket_samples=96,force_python=a.force_python,auto_build=(not a.no_auto_build) if i==0 else False,reach_pair_points=512)
        roots=[r for r in atlas['roots'] if r['classification']=='RESOLVED_LOCAL_MINIMUM' and r['station']==a.station and r['angle_index']==a.angle_index]
        if not roots: raise SystemExit(f'no resolved seed for {k} station={a.station} angle={a.angle_index}')
        seed={**roots[0], 'directions':[roots[0]['azimuthal_seed_direction'],[-v for v in roots[0]['azimuthal_seed_direction']]]}
        curve=sample_ideal_knot(k,a.centerline_points)
        shot=shoot_closed_orbit(curve,seed,epsilon=a.epsilon,step_count=a.steps,max_iterations=a.max_iterations,
            position_tolerance_over_rc=a.position_tol,direction_tolerance=a.direction_tol,force_python=a.force_python,auto_build=False)
        if a.require_native and shot.get('best',{}).get('integration',{}).get('backend',{}).get('backend')!='cpp': raise SystemExit('native backend required')
        results[k]={'candidate_atlas':atlas,'shot':shot}; write_json(out/f'{k}.json',results[k])
        rows.append({'knot_id':k,'status':shot['status'],'resolved_closed_orbit':shot.get('resolved_closed_orbit',False),
            'position_closure_norm_over_rc':shot.get('best',{}).get('position_closure_norm_over_rc'),'direction_closure_norm':shot.get('best',{}).get('direction_closure_norm')})
    combined={'schema':'sst.fermat.geodesic-shooting-matrix.v0.5.0','rows':rows,'results':results,'global_closed_orbit_certified':False,'qsm_certified':False}
    write_json(out/'geodesic_shooting.json',combined); print(json.dumps(rows,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
