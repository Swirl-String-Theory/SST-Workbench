#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from fermat_ext.core import write_json, backend_biot_savart_with_jacobian
from fermat_ext.hole_bundle import HoleBundleParameters,bundle_beta_and_jacobian,estimate_axial_hole_radius,clock_chain,fit_rigid_motion
from fermat_ext.knot_catalog import sample_ideal_knot

def main()->int:
 p=argparse.ArgumentParser(description='v0.6.0 divergence-free coaxial hole-bundle residual sweep.')
 p.add_argument('--knot',default='3_1'); p.add_argument('--epsilon',type=float,default=.0019); p.add_argument('--centerline-points',type=int,default=8192)
 p.add_argument('--radius-ratios',nargs='+',type=float,default=[.5,.75,1,1.25,1.5,2]); p.add_argument('--circulation-ratios',nargs='+',type=float,default=[-2,-1,-.5,0,.5,1,2]); p.add_argument('--return-radius-factor',type=float,default=3.)
 p.add_argument('--force-python',action='store_true'); p.add_argument('--no-auto-build',action='store_true'); p.add_argument('--require-native',action='store_true'); p.add_argument('--out-dir',default='v0.6.0_hole_bundle_output')
 a=p.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True); curve=sample_ideal_knot(a.knot,a.centerline_points); rh=estimate_axial_hole_radius(curve)
 kb,_,backend=backend_biot_savart_with_jacobian(curve.tolist(),curve.tolist(),epsilon=a.epsilon,force_python=a.force_python,auto_build=not a.no_auto_build); knot=np.asarray(kb,float)
 if a.require_native and backend.get('backend')!='cpp': raise SystemExit('native backend required')
 basefit=fit_rigid_motion(curve,knot); base=basefit['relative_shape_residual']; baseline={'backend':backend,'fit':basefit,'knot_beta_rms':float(np.sqrt(np.mean(np.sum(knot*knot,axis=1))))}
 rows=[]; details={}
 for rr in a.radius_ratios:
  rb=rr*rh
  for gr in a.circulation_ratios:
   bundle=HoleBundleParameters(core_radius_over_rc=rb,return_radius_over_rc=max(a.return_radius_factor*rb,rb+1e-6),circulation_ratio=gr)
   bg,_=bundle_beta_and_jacobian(curve,bundle); total=knot+bg; fit=fit_rigid_motion(curve,total); key=f'R{rr:g}_G{gr:g}'
   val=fit['relative_shape_residual']; gain=1-val/base if base>0 else None
   detail={'bundle':bundle.__dict__,'fit':fit,'bundle_beta_rms':float(np.sqrt(np.mean(np.sum(bg*bg,axis=1)))),'total_beta_max':float(np.max(np.linalg.norm(total,axis=1)))}; details[key]=detail
   rows.append({'radius_ratio_to_hole':rr,'bundle_radius_over_rc':rb,'circulation_ratio':gr,'shape_residual':val,'baseline_residual':base,'bundle_gain':gain,'stabilizing':bool(gain is not None and gain>0),'total_beta_max':detail['total_beta_max'],'clock_chain':clock_chain(bundle)})
 rows.sort(key=lambda x:x['shape_residual']); combined={'schema':'sst.fermat.hole-bundle-sweep.v0.6.0','status':'RESEARCH_TRACK_SWEEP_COMPLETED','knot_id':a.knot,'epsilon_over_rc':a.epsilon,'centerline_points':a.centerline_points,'estimated_hole_radius_over_rc':rh,'baseline':baseline,'rows':rows,'best':rows[0] if rows else None,'details':details,'bundle_model':'smooth coaxial central flux plus opposite return flux in a periodic axial cell','physical_finite_closed_bundle_certified':False,'global_closed_orbit_certified':False,'qsm_certified':False}; write_json(out/'hole_bundle_sweep.json',combined); print(json.dumps({'baseline':base,'best':combined['best']},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
