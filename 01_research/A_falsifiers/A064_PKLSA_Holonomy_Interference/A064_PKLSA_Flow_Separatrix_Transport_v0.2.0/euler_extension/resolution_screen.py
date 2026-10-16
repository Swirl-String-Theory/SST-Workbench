"""Coarse two-grid diagnostic only; not a spatial-convergence certificate."""
import json
import numpy as np
from pathlib import Path
from scipy.interpolate import RegularGridInterpolator
from .spectral import SpectralEuler3D,init_knotted_tube,evolve
ROOT=Path(__file__).resolve().parents[1]

def comparison(knot='3_1',lo_n=24,hi_n=32,duration=.36,core=.58):
    pts=np.loadtxt(ROOT/'data'/'PKLSA_RAW_NATIVE_UNQUALIFIED'/f'knot_{knot.replace("_",".")}.txt')
    rows=[]
    for n in (lo_n,hi_n):
        solver=SpectralEuler3D(n)
        u,_=init_knotted_tube(solver,pts,core=core)
        times,v,diag=evolve(solver,u,duration=duration,frame_count=13)
        rows.append({'n':n,'x':(np.arange(n)-n//2)*solver.dx,'v0':v[0], 'v1':v[-1], 'diag':diag})
    high=rows[1];low=rows[0]
    x=low['x'];P=np.stack(np.meshgrid(x,x,x,indexing='ij'),axis=-1).reshape(-1,3)
    def sample(frame):
        return np.stack([RegularGridInterpolator((high['x'],)*3,frame[...,j],bounds_error=False,fill_value=np.nan)(P).reshape(frame.shape[:3]) if False else RegularGridInterpolator((high['x'],)*3,frame[...,j],bounds_error=False,fill_value=np.nan)(P).reshape((lo_n,)*3) for j in range(3)],axis=-1)
    a0=sample(high['v0']);a1=sample(high['v1']);good=np.isfinite(a0).all(axis=-1)&np.isfinite(a1).all(axis=-1)
    def err(a,b):return float(np.linalg.norm((a-b)[good])/max(np.linalg.norm(b[good]),1e-30))
    return {'knot':knot,'coarse_grid':lo_n,'fine_grid':hi_n,'duration':duration,'core':core,
     'initial_velocity_rel_l2_error_coarse_to_fine':err(low['v0'],a0),
     'final_velocity_rel_l2_error_coarse_to_fine':err(low['v1'],a1),
     'diagnostics_coarse':low['diag'],'diagnostics_fine':high['diag'],
     'scientific_status':'TWO_GRID_SCREENING_ONLY_NOT_CONVERGENCE_CERTIFICATION',
     'note':'Comparison uses periodic Euler dimensionless grid; geometry source is not E011 production anchor.'}
if __name__=='__main__':
    j=comparison()
    dst=ROOT/'A064-v0.2.0-outputs'/'RESOLUTION_SCREEN.json'
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(j,indent=2))
    print('two-grid 3_1',j['initial_velocity_rel_l2_error_coarse_to_fine'],j['final_velocity_rel_l2_error_coarse_to_fine'])
