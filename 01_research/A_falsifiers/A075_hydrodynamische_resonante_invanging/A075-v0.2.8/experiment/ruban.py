"""Hash-pinned analytic Ruban T(2,3) seed. Mathematical seed fidelity only."""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
import numpy as np
B0=77/500
DELTA=1/20
LAMBDA=7/5+math.log(200)/2
XI=math.exp(-7/5)/math.sqrt(200)
PRIMARY='RUBAN_T23_B0_0p154_N2048_EQUAL_ARCLENGTH.xyz'
CONTROL_B0=.32

def analytic_torus(b0=B0,n=2048):
    if not 0<b0<1 or n<12:raise ValueError('invalid analytic torus')
    t=np.arange(n,dtype=np.float64)*2*math.pi/n
    return np.column_stack(((1+b0*np.cos(3*t))*np.cos(2*t),
                            (1+b0*np.cos(3*t))*np.sin(2*t),b0*np.sin(3*t)))

def _sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load_primary_seed(path):
    p=Path(path)
    if not p.is_file():raise FileNotFoundError('Ruban exact seed missing: '+str(p))
    manifest=json.loads((p.parent/'SEED_MANIFEST.json').read_text(encoding='utf8'))
    row=next((z for z in manifest['files'] if z['filename']==p.name and z['role']=='primary'),None)
    if row is None or row['sha256']!=_sha(p):raise ValueError('RUBAN_SEED_SHA256_MISMATCH')
    xyz=np.loadtxt(p,comments='#',usecols=(0,1,2))
    if xyz.shape!=(2048,3) or not np.isfinite(xyz).all():raise ValueError('Ruban seed shape or non-finite numbers')
    return xyz, {'kind':'3_1','source':'RUBAN_ANALYTIC_RECONSTRUCTION',
        'source_file':p.name,'sha256':row['sha256'],'B0':B0,'delta_regulator':DELTA,
        'Lambda':LAMBDA,'author_perturbation':'UNKNOWN_NOT_REPRODUCED',
        'topology_verification':'ANALYTIC_WINDINGS_ONLY_NOT_DYNAMICAL_TRACKING'}

def verify_geometry(path):
    xyz,pr=load_primary_seed(path)
    xy=np.hypot(xyz[:,0],xyz[:,1]);major=1.
    rr=np.hypot(xy-major,xyz[:,2])
    toroidal=np.unwrap(np.arctan2(xyz[:,1],xyz[:,0]))
    poloidal=np.unwrap(np.arctan2(xyz[:,2],xy-major))
    # Include closure segment when calculating winding numbers.
    def winding(angle):
        wrap=(angle[0]-angle[-1]+np.pi)%(2*np.pi)-np.pi
        return (angle[-1]-angle[0]+wrap)/(2*np.pi)
    legs=np.linalg.norm(np.roll(xyz,-1,axis=0)-xyz,axis=1)
    tw,pw=winding(toroidal),winding(poloidal)
    m={'schema':'A075-RUBAN-SEED-FIDELITY-1','seed_sha256':pr['sha256'],
        'B0_exact':'77/500','delta_exact':'1/20','Lambda_exact':'7/5 + log(200)/2',
        'B0_float':B0,'delta_filament':DELTA,'Lambda_float':LAMBDA,
        'R0':major,'r0_measured_min':float(rr.min()),'r0_measured_max':float(rr.max()),
        'max_r0_residual':float(np.max(np.abs(rr-B0))),
        'toroidal_winding':float(tw),'poloidal_winding':float(pw),
        'points':len(xyz),'segment_ratio_max_min':float(legs.max()/legs.min()),
        'closed_segment_length':float(legs.sum()),
        'author_perturbation_reconstructed':False,
        'paper_trajectory_reproduced':False,
        'topology_certified_during_evolution':False}
    m['geometric_fidelity_pass']=bool(m['max_r0_residual']<1e-12 and abs(abs(tw)-2)<1e-7
       and abs(abs(pw)-3)<1e-7 and m['segment_ratio_max_min']<1.00001)
    return m

def resolution_gate(box,grid,sigma):
    dx=box/grid
    return {'grid':grid,'box':box,'dx':dx,'rminor_cells':B0/dx,
        'delta_cells_IF_misinterpreted_as_Euler_sigma':DELTA/dx,
        'xi_cells_IF_misinterpreted_as_Euler_sigma':XI/dx,
        'euler_gaussian_sigma':sigma,'sigma_cells':sigma/dx,
        'sigma_over_rminor':sigma/B0,'euler_core_not_ruban_delta':True,
        'ruban_filament_regime_reproduced':False,
        'spatial_fidelity_qualified':False}
