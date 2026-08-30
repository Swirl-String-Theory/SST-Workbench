from pathlib import Path
import math
import numpy as np
from .solver import velocity,stretch_rate,rk4,backend_name,segment_lengths

def integration_plan(xref,cfg):
    xref=np.asarray(xref,float)
    gamma=float(cfg.get("gamma_dimensionless",1.0))
    dsref=float(np.min(segment_lengths(xref)))
    dt_target=float(cfg.get("dt_factor",.02))*dsref**2/max(abs(gamma),1e-30)
    T=float(cfg["t_final"])
    required_steps=max(8,int(math.ceil(T/dt_target)))
    max_steps=int(cfg.get("max_steps",200000))
    if required_steps>max_steps:
        raise RuntimeError(
            f"required_steps={required_steps} exceeds max_steps={max_steps}; "
            "refusing to enlarge dt because that would violate the configured dt~ds^2 policy"
        )
    dt=T/required_steps
    max_samples=int(cfg.get("max_samples",320))
    stride=max(1,int(math.ceil(required_steps/max_samples)))
    return {"steps":required_steps,"dt":dt,"dt_target":dt_target,"stride":stride,"ds_reference":dsref}

def simulate(x0,xref,ref_lengths,cfg,out,core_mode):
    x=np.asarray(x0,float).copy(); xref=np.asarray(xref,float); ref=np.asarray(ref_lengths,float)
    gamma=float(cfg.get('gamma_dimensionless',1)); core0=float(cfg['core_fraction']); exp=-.5 if core_mode=='material' else 0.0; req=bool(cfg.get('require_native',True))
    plan=integration_plan(xref,cfg); steps=int(plan['steps']); dt=float(plan['dt']); stride=int(plan['stride'])
    ts=[]; xs=[]; sig=[]; dscv=[]; corecv=[]
    for k in range(steps+1):
        if k%stride==0 or k==steps:
            u,cores=velocity(x,gamma,core0,ref,exp,req); sr=stretch_rate(x,u); ds=segment_lengths(x)
            ts.append(k*dt); xs.append(x.copy()); sig.append(sr.copy()); dscv.append(float(ds.std()/max(ds.mean(),1e-30))); corecv.append(float(cores.std()/max(cores.mean(),1e-30)))
        if k<steps: x=rk4(x,dt,gamma,core0,ref,exp,req)
        if not np.isfinite(x).all(): raise FloatingPointError('non-finite geometry')
    np.savez_compressed(out,t=np.asarray(ts),x=np.asarray(xs),sigma=np.asarray(sig),x_reference=xref,reference_lengths=ref,ds_cv=np.asarray(dscv),core_cv=np.asarray(corecv),dt=dt,dt_target=float(plan['dt_target']),steps=steps,core_mode=core_mode,backend=backend_name())
    return {'samples':len(ts),'steps':steps,'dt':dt,'dt_target':float(plan['dt_target']),'max_ds_cv':float(max(dscv)),'max_core_cv':float(max(corecv)),'core_mode':core_mode,'backend':backend_name()}
