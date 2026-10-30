"""Fail-closed Framework v1.1.0 scientific pipeline hook.

The physical mechanism gates G3/G4/G7/G8 are deliberately UNRESOLVED until
independent 3-D Euler field providers and spinor topological proof exist.
"""
from pathlib import Path
import json
import numpy as np
from science.ring_model import trajectory, axial_order_crossings


def run_scientific_pipeline(root, cfg, ledger, mode):
 root=Path(root)
 c=json.loads((root/'configs'/'pilot.json').read_text())
 ledger.record('G0','PASS',metrics={'mode':mode},reason='Framework verified preregistration and embedded runtime bootstrap.')
 data=c['initial_conditions_dimensionless']['same']
 y=np.column_stack((data['radii'],data['z'])).ravel()
 gamma=data['gamma_signs'];a=np.asarray(data['radii'])*c['core_ratio']
 fixed_T=float(c['normalized_time_end'])
 def G1():
  return {'status':'PASS','reason':'Analytic, deterministic two-ring seed without external dataset.'}
 def G2():
  levels=[]
  for n in c['spatial_refinement_ntheta']:
   s=trajectory(y,gamma,a,dt=fixed_T/c['pilot_steps'],steps=c['pilot_steps'],ntheta=n)
   levels.append(s['y'][-1])
  err=float(np.linalg.norm(levels[-1]-levels[-2])/max(np.linalg.norm(levels[-1]),1e-14))
  return {'status':'PASS' if err<=c['spatial_relative_tolerance'] else 'FAIL',
      'reason':'Angular-quadrature convergence for reduced ring model only, not 3D Euler.',
      'metrics':{'angular_quadrature_relative_difference':err,'full_euler_certified':False}}
 def unresolved(label):return lambda:{'status':'UNRESOLVED','reason':label}
 # Framework non-short-circuit diagnostics: observed gate != qualified physical claim.
 evals={'G1':G1,'G2':G2,
   'G3':unresolved('No blind spectral discrete-level discovery with full-field Euler.'),
   'G4':unresolved('No independent held-out finite-core field confirmation.'),
   'G5':unresolved('Use framework backend matrix; independently check native pybind11 parity, not a dummy PASS.'),
   'G6':unresolved('GPU kernel not implemented; device probes cannot count.'),
   'G7':unresolved('Only analytic initial family; refinement not independent replication.'),
   'G8':unresolved('No full 3D Euler, independent toroidal circulation, jet flow, or spinor representation.')}
 ledger.run_evaluators(evals)
 return {'schema':'SST-BACKEND-MANIFEST-2','model':'AXISYMMETRIC_REGULARIZED_FILAMENT_PROXY',
   'scientific_authority':'DEVELOPMENT_DIAGNOSTIC_ONLY',
   'note':'P01-P03 local diagnostics; P04-P07 and spinorial claim unresolved.'}
