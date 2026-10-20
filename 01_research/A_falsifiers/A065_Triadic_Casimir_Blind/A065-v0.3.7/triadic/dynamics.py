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
    """Numerical qualification: nested 75/150/300 grids, fixed eps, gamma, T.

    All grids are reductions of the SAME upstream geometry, not providers.
    Never increase or retune the finite core as grid size changes.
    """
    root=Path(root);base=root/'data'/'D01_EULER'/'pklsa'
    conf=readjson(base/'filament_dynamics_protocol.json')
    source=readjson(base/'source.json')
    spec=readjson(root/'preregistration'/'QUALIFICATION_V031.json')
    original=base/source['source_file']
    import hashlib
    if hashlib.sha256(original.read_bytes()).hexdigest()!=source['raw_sha256']:
        raise RuntimeError('PKLSA geometry source hash failed')
    points=load_geometry(original)
    if len(points)!=300 or spec['geometry_points']!=[75,150,300]:
        raise RuntimeError('preregistered geometry ladder missing')
    core=float(conf['core_epsilon']);gamma=float(conf['gamma']);T=float(conf['final_time'])
    nc=int(conf['step_count_coarse']);nf=int(conf['step_count_fine'])
    if (core,gamma,T,nc,nf)!=(spec['fixed_epsilon'],spec['fixed_gamma'],spec['fixed_final_time'],
                              spec['integration_step_count_coarse'],spec['integration_step_count_fine']):
        raise RuntimeError('PHYSICAL_NUMERICAL_PARAMETERS_CHANGED_AFTER_PREREGISTRATION')
    levels={75:points[::4],150:points[::2],300:points}
    # Only the 75-node trajectory is needed for the original time-halving gate.
    rough=evolve(levels[75],core,gamma,T,nc)
    traces={n:evolve(levels[n],core,gamma,T,nf) for n in (75,150,300)}
    error=rms_difference(rough,traces[75]); disp75=rms_difference(levels[75],traces[75])
    def pair(n,m,stride):
        x,y=traces[n],traces[m][::stride]
        spatial=rms_difference(x,y)
        # Preserve v0.3.0 denominator (displacement on coarser grid) for historical comparability.
        base_disp=rms_difference(levels[n],traces[n])
        return {'rms':spatial,'relative':spatial/max(1e-14,base_disp),
                'denominator_coarse_displacement':base_disp,
                'relative_threshold':spec['spatial_relative_threshold'],
                'gate':'PASS' if spatial/max(1e-14,base_disp)<spec['spatial_relative_threshold'] else 'FAIL'}
    pairs={'75_vs_150':pair(75,150,2),'150_vs_300':pair(150,300,2),'75_vs_300':pair(75,300,4)}
    max_shift=max(math.dist(p,q) for p,q in zip(levels[75],traces[75]))
    diag={'schema':'A065-FILAMENT-DYNAMICS-2','algorithm':'RK4 fixed-core segment Biot-Savart; nested grid ladder',
        'source_raw_sha256':source['raw_sha256'],'simulation_evidence_class':'simulation',
        'node_count':75,'resolution_ladder':[75,150,300],
        'gamma':gamma,'regularization':core,'t_final':T,
        'dt_coarse':T/nc,'dt_fine':T/nf,
        'rms_coarse_fine_difference':error,
        'relative_discretization_error':error/max(1e-14,disp75),
        'rms_displacement':disp75,
        'centroid_shift':math.dist(centroid(levels[75]),centroid(traces[75])),
        'relative_arclength_change':(length(traces[75])-length(levels[75]))/length(levels[75]),
        'max_point_displacement':max_shift,
        'spatial_pairs':pairs,
        'spatial_75_150_rms_difference':pairs['75_vs_150']['rms'],
        'spatial_75_150_relative_displacement':pairs['75_vs_150']['relative'],
        'spatial_150_300_rms_difference':pairs['150_vs_300']['rms'],
        'spatial_150_300_relative_displacement':pairs['150_vs_300']['relative'],
        'spatial_75_300_relative_displacement':pairs['75_vs_300']['relative'],
        'predeclared_ladder_complete':True,
        'numerical_gate':None,
        'physics_qualification':'NOT_VALIDATED_AS_EULER; NO_FLOQUET; NO_ATOMIC_MODE; NO_METAL_RESPONSE'}
    ok=(math.isfinite(error) and error/max(disp75,1e-14)<conf['pointwise_rel_tolerance']
        and disp75>conf['centroid_shift_min'] and max_shift<conf['max_displacement_limit'])
    diag['numerical_gate']='PASS' if ok else 'FAIL'
    return diag
