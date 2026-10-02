#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from fermat_ext.certification import scan_stationary_candidates
from fermat_ext.core import write_json
from fermat_ext.geodesic import shoot_closed_orbit, compute_reduced_monodromy
from fermat_ext.knot_catalog import sample_ideal_knot


def main() -> int:
    p=argparse.ArgumentParser(description='Fast single-level monodromy pipeline smoke test.')
    p.add_argument('--force-python',action='store_true'); p.add_argument('--no-auto-build',action='store_true'); p.add_argument('--require-native',action='store_true')
    p.add_argument('--out-dir',default='monodromy_smoke'); a=p.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    atlas=scan_stationary_candidates('0_1',epsilon=.0019,centerline_points=2048,stations=1,angles=3,rho_min=.0005,rho_max=.01,bracket_samples=48,force_python=a.force_python,auto_build=not a.no_auto_build,reach_pair_points=128)
    roots=[r for r in atlas['roots'] if r['classification']=='RESOLVED_LOCAL_MINIMUM']
    if not roots: raise SystemExit('no 0_1 smoke seed')
    r=roots[0]; seed={**r,'directions':[r['azimuthal_seed_direction'],[-v for v in r['azimuthal_seed_direction']]]}; curve=sample_ideal_knot('0_1',2048)
    shot=shoot_closed_orbit(curve,seed,epsilon=.0019,step_count=32,max_iterations=0,force_python=a.force_python,auto_build=False)
    monodromy=compute_reduced_monodromy(curve,shot,epsilon=.0019,position_perturbation_fraction=1e-5,direction_perturbation=1e-5,force_python=a.force_python,auto_build=False)
    backend=shot.get('best',{}).get('integration',{}).get('backend',{}).get('backend')
    if a.require_native and backend!='cpp': raise SystemExit('native backend required')
    result={'schema':'sst.fermat.monodromy-smoke.v0.5.0','shot':shot,'monodromy':monodromy,'pipeline_ok':True,'global_closed_orbit_certified':False,'monodromy_certified':False,'qsm_certified':False}
    write_json(out/'monodromy_smoke.json',result); print(json.dumps({'pipeline_ok':True,'shot_status':shot['status'],'classification':monodromy['classification']},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
