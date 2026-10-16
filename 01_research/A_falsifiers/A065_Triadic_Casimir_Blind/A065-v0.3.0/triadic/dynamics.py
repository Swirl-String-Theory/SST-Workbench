"""Pre-registered *approximate* regularized filament ODE, not Euler certification.

Uniform 75-node subsample of one authenticated PKLSA / KnotPlot 3_1 geometry,
regularized segment midpoint velocity evaluated at advected nodes, RK4, dt
halving check at fixed final time. All constants dimensionless, no force fit.
"""
from __future__ import annotations
import math, json
from pathlib import Path
from .pklsa import load_geometry
from .security import readjson

PI4=4.0*math.pi

def velocities(pts,core,gamma=1.0):
    n=len(pts)
    mids=[tuple((pts[j][d]+pts[(j+1)%n][d])/2 for d in range(3)) for j in range(n)]
    segs=[tuple(pts[(j+1)%n][d]-pts[j][d] for d in range(3)) for j in range(n)]
    out=[]
    for x in pts:
        acc=[0.,0.,0.]
        for m,s in zip(mids,segs):
            rx=x[0]-m[0];ry=x[1]-m[1];rz=x[2]-m[2]
            inv=(rx*rx+ry*ry+rz*rz+core*core)**(-1.5)
            acc[0]+=(s[1]*rz-s[2]*ry)*inv
            acc[1]+=(s[2]*rx-s[0]*rz)*inv
            acc[2]+=(s[0]*ry-s[1]*rx)*inv
        out.append(tuple(gamma*v/PI4 for v in acc))
    return out

def add_scaled(y,k,a):
    return [tuple(y[i][d]+a*k[i][d] for d in range(3)) for i in range(len(y))]

def step_rk4(y,dt,core,gamma):
    k1=velocities(y,core,gamma)
    k2=velocities(add_scaled(y,k1,dt/2),core,gamma)
    k3=velocities(add_scaled(y,k2,dt/2),core,gamma)
    k4=velocities(add_scaled(y,k3,dt),core,gamma)
    return [tuple(y[i][d]+dt*(k1[i][d]+2*k2[i][d]+2*k3[i][d]+k4[i][d])/6 for d in range(3)) for i in range(len(y))]

def evolve(y,core,gamma,tfinal,nsteps):
    a=[tuple(v) for v in y];dt=tfinal/nsteps
    for _ in range(nsteps): a=step_rk4(a,dt,core,gamma)
    return a

def rms_difference(a,b):
    return math.sqrt(sum((v[d]-w[d])**2 for v,w in zip(a,b) for d in range(3))/len(a))

def centroid(a):
    return [sum(row[j] for row in a)/len(a) for j in range(3)]

def length(a):
    return sum(math.dist(a[j],a[(j+1)%len(a)]) for j in range(len(a)))

def run(root):
    root=Path(root);base=root/'data'/'D01_EULER'/'pklsa'
    conf=readjson(base/'filament_dynamics_protocol.json')
    source=readjson(base/'source.json')
    original=base/source['source_file']
    import hashlib
    if hashlib.sha256(original.read_bytes()).hexdigest()!=source['raw_sha256']:raise RuntimeError('PKLSA geometry source hash failed')
    points=load_geometry(original)
    assert len(points)==300 and conf['nodes']==75
    sampled=points[::4]
    core=conf['core_epsilon'];gam=conf['gamma'];T=conf['final_time']
    nc=conf['step_count_coarse'];nf=conf['step_count_fine']
    c=evolve(sampled,core,gam,T,nc)
    f=evolve(sampled,core,gam,T,nf)
    error=rms_difference(c,f); displacement=rms_difference(sampled,f)
    finer=evolve(points[::2],core,gam,T,nf)
    spatial_error=rms_difference(f,finer[::2])
    diagnostics={'schema':'A065-FILAMENT-DYNAMICS-1','algorithm':'RK4 regularized finite-core segment Biot-Savart',
        'source_raw_sha256':source['raw_sha256'],'simulation_evidence_class':'simulation',
        'node_count':len(sampled),'gamma':gam,'regularization':core,
        't_final':T,'dt_coarse':T/nc,'dt_fine':T/nf,
        'rms_coarse_fine_difference':error,
        'spatial_75_150_rms_difference':spatial_error,
        'spatial_75_150_relative_displacement':spatial_error/max(displacement,1e-14),
        'relative_discretization_error':error/max(1e-14,displacement),
        'rms_displacement':displacement,
        'centroid_shift':math.dist(centroid(sampled),centroid(f)),
        'relative_arclength_change':(length(f)-length(sampled))/length(sampled),
        'max_point_displacement':max(math.dist(x,y) for x,y in zip(sampled,f)),
        'numerical_gate':None,
        'physics_qualification':'NOT_VALIDATED_AS_EULER; NO_FLOQUET; NO_ATOMIC_MODE; NO_METAL_RESPONSE'}
    ok=(math.isfinite(error) and error/max(displacement,1e-14) < conf['pointwise_rel_tolerance']
        and displacement>conf['centroid_shift_min'] and diagnostics['max_point_displacement']<conf['max_displacement_limit'])
    diagnostics['numerical_gate']='PASS' if ok else 'FAIL'
    return diagnostics
