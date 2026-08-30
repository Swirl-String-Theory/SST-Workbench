import math
from pathlib import Path
import numpy as np
from .solver import velocity_material,stretch_rate,rk4_step_material,backend_name,segment_lengths
from .geometry import radius_gyration
from .observables import length,segment_quality

def simulate(x0,cfg,out_npz,reference_lengths=None,dt_reference_ds=None):
    x=np.asarray(x0,float).copy(); gamma=float(cfg.get('gamma_dimensionless',1.0)); core0=float(cfg['core_fraction']); require_native=bool(cfg.get('require_native',True))
    core_exp=float(cfg.get('core_length_exponent',-0.5))
    ref_lengths=segment_lengths(x).copy() if reference_lengths is None else np.asarray(reference_lengths,float).copy()
    if len(ref_lengths)!=len(x): raise ValueError('reference_lengths size mismatch')
    ds_now=segment_lengths(x); ds_ref=float(dt_reference_ds) if dt_reference_ds is not None else float(ds_now.min()); dt=float(cfg.get('dt_factor',0.02))*float(ds_ref**2)/max(abs(gamma),1e-30)
    T=float(cfg['t_final']); max_steps=int(cfg.get('max_steps',200000)); steps=min(max_steps,max(4,int(math.ceil(T/dt)))); dt=T/steps
    stride=max(1,int(cfg.get('sample_stride',max(1,steps//400))))
    ts=[]; rgs=[]; lens=[]; sig=[]; qmin=[]; qmax=[]; cv=[]; speed=[]; core_mean=[]; core_cv=[]; omega_rms=[]; stretch_rms=[]
    xref=x.copy()
    for step in range(steps+1):
        if step%stride==0 or step==steps:
            u,cores=velocity_material(x,gamma,core0,ref_lengths,core_exp,require_native); sr=stretch_rate(x,u); qual=segment_quality(x)
            om=abs(gamma)/(np.pi*np.maximum(cores,1e-15)**2)
            ts.append(step*dt); rgs.append(radius_gyration(x)); lens.append(length(x)); sig.append(sr); qmin.append(qual['ds_min']); qmax.append(qual['ds_max']); cv.append(qual['ds_cv']); speed.append(float(np.sqrt((u*u).sum(1)).mean())); core_mean.append(float(cores.mean())); core_cv.append(float(cores.std()/max(cores.mean(),1e-30))); omega_rms.append(float(np.sqrt(np.mean(om*om)))); stretch_rms.append(float(np.sqrt(np.mean(sr*sr))))
        if step<steps: x=rk4_step_material(x,dt,gamma,core0,ref_lengths,core_exp,require_native)
        if not np.isfinite(x).all(): raise FloatingPointError('non-finite geometry')
    np.savez_compressed(out_npz,t=np.asarray(ts),rg=np.asarray(rgs),length=np.asarray(lens),sigma=np.asarray(sig),ds_min=np.asarray(qmin),ds_max=np.asarray(qmax),ds_cv=np.asarray(cv),mean_speed=np.asarray(speed),core_mean=np.asarray(core_mean),core_cv=np.asarray(core_cv),omega_rms=np.asarray(omega_rms),stretch_rms=np.asarray(stretch_rms),x0=xref,x_final=x,reference_lengths=ref_lengths,dt=dt,steps=steps,backend=backend_name(),core_length_exponent=core_exp)
    return {'dt':dt,'steps':steps,'samples':len(ts),'backend':backend_name(),'core_length_exponent':core_exp,'max_ds_ratio':float(np.max(np.asarray(qmax)/np.maximum(qmin,1e-30))),'max_ds_cv':float(np.max(cv)),'max_core_cv':float(np.max(core_cv))}
