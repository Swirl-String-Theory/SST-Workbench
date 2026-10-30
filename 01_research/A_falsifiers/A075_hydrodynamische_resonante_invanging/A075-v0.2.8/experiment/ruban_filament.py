"""Ruban (2018), Eq. (9) discretized as a finite-difference/midpoint diagnostic.

This is NOT the author's pseudo-spectral filament solver and not the
unspecified weakly perturbed initial state. Do not claim paper-lifetime replication.
Units: R0=1, Gamma=2*pi, rho=1; delta=0.05, Lambda0tilde/2=(1.4-.5 log2)/2.
"""
from __future__ import annotations
import csv,json,math
from pathlib import Path
import numpy as np
from .ruban import PRIMARY,DELTA,B0,LAMBDA,load_primary_seed,analytic_torus
from .euler3d import resample_closed
from .heartbeat import phase,advance
C_LOCAL=(7/5-math.log(2)/2)/2


def velocity(p, *, delta=DELTA, local_coefficient=C_LOCAL,block=128):
    """Eq.9: 1/2 sum_j dl_j x (x_i - mid_j)/(r_ij^2+delta^2)^1.5
    plus local induction (Lambda_tilde0/2) * kappa*b.
    Quadrature/discrete curvature errors require convergence tests.
    """
    p=np.asarray(p,dtype=np.float64)
    if p.ndim!=2 or p.shape[1]!=3 or len(p)<16 or not np.isfinite(p).all():
        raise ValueError('Invalid filament geometry')
    if delta<=0:raise ValueError('delta must be positive')
    d=np.roll(p,-1,axis=0)-p
    mids=p+d/2
    out=np.empty_like(p)
    for j in range(0,len(p),block):
        r=p[j:j+block,None,:]-mids[None,:,:]
        den=(np.sum(r*r,axis=-1)+delta**2)**1.5
        out[j:j+block]=.5*np.sum(np.cross(d[None,:,:],r)/den[:,:,None],axis=1)
    # Curvature binormal from the geometrically invariant local chord spacing.
    ds=np.linalg.norm(d,axis=-1)
    h=float(np.mean(ds))
    d1=(np.roll(p,-1,axis=0)-np.roll(p,1,axis=0))/(2*h)
    d2=(np.roll(p,-1,axis=0)-2*p+np.roll(p,1,axis=0))/h**2
    kbin=np.cross(d1,d2)/np.maximum(np.linalg.norm(d1,axis=1)**3,1e-20)[:,None]
    return out+local_coefficient*kbin

def hamiltonian(p,*,delta=DELTA,local_coefficient=C_LOCAL):
    # Ruban Eqs.6,7 with rho=1 and Gamma=2pi, approximate line integrals.
    ds=np.roll(p,-1,axis=0)-p;m=p+ds/2
    pair=m[:,None,:]-m[None,:,:]
    den=np.sqrt(np.sum(pair**2,axis=-1)+delta**2)
    K=(math.pi/2)*float(np.sum((ds@ds.T)/den))
    U=(2*math.pi*local_coefficient)*float(np.sum(np.linalg.norm(ds,axis=-1)))
    return K+U

def rk4(p,dt,**kwargs):
    k1=velocity(p,**kwargs);k2=velocity(p+dt*k1/2,**kwargs)
    k3=velocity(p+dt*k2/2,**kwargs);k4=velocity(p+dt*k3,**kwargs)
    return p+dt*(k1+2*k2+2*k3+k4)/6

def kabsch_rms(a,b):
    """Min RMS after proper rotation+translation AND cyclic relabeling.
    This is a geometric proxy, not knot-type detection.
    """
    a=np.asarray(a);b=np.asarray(b);ac=a-a.mean(axis=0);bc=b-b.mean(axis=0)
    best=float('inf')
    for shift in range(len(a)):
        m=np.roll(ac,shift,axis=0)
        U,_,V=np.linalg.svd(m.T@bc)
        D=np.eye(3);D[2,2]=np.sign(np.linalg.det(U@V))
        rot=U@D@V
        err=float(np.sqrt(np.mean(np.sum((m@rot-bc)**2,axis=1))))
        best=min(best,err)
    return best

def evolve(p,T=.04,dt=.005,*,delta=DELTA,local_coefficient=C_LOCAL,max_steps=10000):
    p=np.array(p,dtype=np.float64,copy=True);orig=p.copy()
    if not 0<T and 0<dt:raise ValueError('Invalid time')
    initialH=hamiltonian(p,delta=delta,local_coefficient=local_coefficient)
    t=0.;i=0;series=[];stop=None
    def sample():
        seg=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
        H=hamiltonian(p,delta=delta,local_coefficient=local_coefficient)
        series.append({'t':t,'step':i,'hamiltonian':H,
             'hamiltonian_relative_drift':(H-initialH)/max(abs(initialH),1e-30),
             'segment_ratio_max_min':float(seg.max()/seg.min()),
             'rms_best_rigid_cyclic':kabsch_rms(p,orig),
             'centroid_z':float(np.mean(p[:,2]))})
    sample()
    while t<T-1e-13:
        if i>=max_steps:stop='MAX_STEPS';break
        step=min(dt,T-t);q=rk4(p,step,delta=delta,local_coefficient=local_coefficient)
        if not np.isfinite(q).all():stop='NONFINITE';break
        p=q;t=min(T,t+step);i+=1;advance(i,t,T,step)
        if i%max(1,round(T/dt/15))==0 or t>=T-1e-13:sample()
        if series[-1]['segment_ratio_max_min']>3:
            stop='MESH_DEGENERATION_RATIO_GT_3';break
    return {'schema':'A075-RUBAN-EQ9-FILAMENT-MIDPOINT_DIAGNOSTIC-1',
            'time_final':t,'time_target':T,'steps':i,'stop':stop,
            'delta_regulator':delta,'local_coefficient':local_coefficient,
            'initial_hamiltonian':initialH,'final_hamiltonian':series[-1]['hamiltonian'],
            'relative_drift_max':max(abs(x['hamiltonian_relative_drift']) for x in series),
            'rigid_cyclic_rms_final':series[-1]['rms_best_rigid_cyclic'],
            'series':series,'physical_stability':'UNRESOLVED',
            'paper_trajectory_reproduced':False,'full_pseudospectral_method_used':False,
            'filament_topology_tracking_certified':False}

def run_filament_study(root,out,*,n=128,T=.04,dt=.005,include_control=True):
    root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    if n<32 or n>512 or n%16:raise ValueError('filament points 32..512, multiple of 16')
    xyz,provenance=load_primary_seed(root/'inputs/ruban_t23'/PRIMARY)
    choices=[('ruban',resample_closed(xyz,n))]
    if include_control:choices.append(('analytic_032',resample_closed(analytic_torus(.32,2048),n)))
    cases={}
    for idx,(label,p) in enumerate(choices,1):
        phase('ruban_eq9_filament',backend='numpy_cpu',knot=label,grid=n,
              physical_end_time=T,phase_index=idx,phase_total=len(choices))
        result=evolve(p,T,dt)
        (out/f'{label}.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        with (out/f'{label}_series.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=result['series'][0]);writer.writeheader();writer.writerows(result['series'])
        cases[label]={k:result[k] for k in ('steps','stop','relative_drift_max',
                                             'rigid_cyclic_rms_final','time_final')}
    summary={'schema':'A075-RUBAN-FILAMENT-SHORT_DIAGNOSTIC-1',
      'paper_delta_exact':'1/20','paper_Lambda_exact':'7/5+ln(200)/2',
      'input_seed_sha256':provenance['sha256'],'n_points':n,
      'solver':'midpoint_Biot_Savart_plus_finite_difference_LIA_RK4',
      'eq9_parameter_equivalence':True,'paper_pseudospectral_discretization_same':False,
      'author_perturbation_reconstructed':False,'paper_t_320_reproduced':False,
      'no_physical_stability_certification':True,'cases':cases,'status':'DIAGNOSTIC_ONLY'}
    (out/'RUBAN_FILAMENT_SUMMARY.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    return summary
