from __future__ import annotations
import numpy as np
from a056_science.numeric import _native_cached
from .geometry import kelvin_perturb,phase_and_ringdown,closed_arclength_resample
from .finite_core import velocity_seed
from .spectral_euler import dealias_mask,rk4_coupled,diagnostics

def _filament_velocity(P,core):
    try: mod,_=_native_cached()
    except Exception: mod=None
    if mod is not None and hasattr(mod,'biot_savart'): return np.asarray(mod.biot_savart(np.ascontiguousarray(P,float),np.ascontiguousarray(P,float),1.0,float(core)))
    P=np.asarray(P,float); n=len(P); out=np.zeros_like(P); a2=core*core; scale=1/(4*np.pi)
    A=P; B=np.roll(P,-1,axis=0); dl=B-A; mid=.5*(A+B)
    for j,x in enumerate(P):
        r=x-mid; den=np.power(np.sum(r*r,axis=1)+a2,1.5); out[j]=scale*np.sum(np.cross(dl,r)/den[:,None],axis=0)
    return out

def _filament_rk4(P,dt,core):
    k1=_filament_velocity(P,core); k2=_filament_velocity(P+.5*dt*k1,core); k3=_filament_velocity(P+.5*dt*k2,core); k4=_filament_velocity(P+dt*k3,core); return P+(dt/6)*(k1+2*k2+2*k3+k4)

def evolve_filament(P,dt,T,core,sample_every):
    P=np.asarray(P,float).copy(); steps=int(round(T/dt)); times=[]; hist=[]; seg_rat=[]
    for n in range(steps+1):
        if n%sample_every==0 or n==steps:
            times.append(n*dt); hist.append(P.copy()); seg=np.linalg.norm(np.roll(P,-1,axis=0)-P,axis=1); seg_rat.append(float(np.max(seg)/max(np.min(seg),1e-30)))
        if n<steps: P=_filament_rk4(P,dt,core)
    return np.asarray(times),np.asarray(hist),{"max_segment_ratio":max(seg_rat),"finite":bool(np.isfinite(hist).all())}

def evolve_euler(P,N,L,sigma,dt,T,sample_every,prefer_native_seed=True):
    uh,seedinfo=velocity_seed(P,N,L,sigma,prefer_native_seed); X=np.asarray(P,float).copy(); mask=dealias_mask(N); steps=int(round(T/dt)); times=[]; hist=[]; diags=[]
    for n in range(steps+1):
        if n%sample_every==0 or n==steps:
            times.append(n*dt); hist.append(X.copy()); diags.append(diagnostics(uh,L))
        if n<steps: uh,X=rk4_coupled(uh,X,dt,L,mask)
    E0=diags[0]['energy']; drift=max(abs(d['energy']-E0)/max(abs(E0),1e-30) for d in diags); div=max(d['div_rms'] for d in diags)
    return np.asarray(times),np.asarray(hist),{"energy_relative_drift_max":float(drift),"div_rms_max":float(div),"seed":seedinfo}

def paired_observables(P,solver,perturb):
    P=np.asarray(P,float); Q,pinfo=kelvin_perturb(P,perturb['epsilon'],perturb['mode'])
    kind=solver['kind']
    if kind=='filament_bs':
        tb,B,db=evolve_filament(P,solver['dt'],solver['T'],solver['core'],solver.get('sample_every',1)); tp,H,dp=evolve_filament(Q,solver['dt'],solver['T'],solver['core'],solver.get('sample_every',1))
        valid=bool(db['finite'] and dp['finite'] and max(db['max_segment_ratio'],dp['max_segment_ratio'])<=solver.get('max_segment_ratio',4.0))
        diag={"kind":kind,"base":db,"perturbed":dp,"provider_numerically_valid":valid}
    elif kind=='euler_ps3d':
        tb,B,db=evolve_euler(P,solver['N'],solver['Lbox'],solver['sigma'],solver['dt'],solver['T'],solver.get('sample_every',1),solver.get('prefer_native_seed',True)); tp,H,dp=evolve_euler(Q,solver['N'],solver['Lbox'],solver['sigma'],solver['dt'],solver['T'],solver.get('sample_every',1),solver.get('prefer_native_seed',True))
        eth=solver.get('energy_drift_max',1e-4); dth=solver.get('div_rms_max',1e-10); valid=bool(max(db['energy_relative_drift_max'],dp['energy_relative_drift_max'])<=eth and max(db['div_rms_max'],dp['div_rms_max'])<=dth)
        dx=solver['Lbox']/solver['N']; diag={"kind":kind,"base":db,"perturbed":dp,"core_points":solver['sigma']/dx,"provider_numerically_valid":valid}
    else: raise ValueError(kind)
    if len(tb)!=len(tp) or np.max(np.abs(tb-tp))>1e-12: raise RuntimeError('paired timelines disagree')
    phi,rt,R,phase_diag=phase_and_ringdown(tb,B,H,P,perturb['mode'],perturb.get('amplitude_floor_fraction',.03)); diag['phase']=phase_diag; diag['provider_numerically_valid'] &= phase_diag['phase_valid_fraction']>=perturb.get('min_phase_valid_fraction',.95)
    Q0=np.vstack([P,P[0]]); s0=np.concatenate([[0.0],np.cumsum(np.linalg.norm(np.diff(Q0,axis=0),axis=1))]); s=s0[:-1]
    return {"t":tb,"s":s,"phi":phi,"ringdown_t":rt,"ringdown":R,"diagnostics":diag,"perturbation":pinfo}
