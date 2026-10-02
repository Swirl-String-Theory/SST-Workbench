from pathlib import Path
import math
import numpy as np
from .solver import velocity,velocity_from_cores,uniform_global_volume_cores,stretch_rate,rk4,backend_name,segment_lengths
from .geometry import tangential_redistribution_velocity

def integration_plan(xref,cfg,t_key='t_final'):
    xref=np.asarray(xref,float); gamma=float(cfg.get('gamma_dimensionless',1.0))
    dsref=float(np.min(segment_lengths(xref))); dt_target=float(cfg.get('dt_factor',.02))*dsref**2/max(abs(gamma),1e-30)
    T=float(cfg[t_key]); required_steps=max(8,int(math.ceil(T/dt_target))); max_steps=int(cfg.get('max_steps',200000))
    if required_steps>max_steps:
        raise RuntimeError(f'required_steps={required_steps} exceeds max_steps={max_steps}; refusing to enlarge dt because that would violate the configured dt~ds^2 policy')
    dt=T/required_steps; max_samples=int(cfg.get('max_samples',320)); stride=max(1,int(math.ceil(required_steps/max_samples)))
    return {'steps':required_steps,'dt':dt,'dt_target':dt_target,'stride':stride,'ds_reference':dsref,'t_final':T}

def _rms(v): return float(np.sqrt(np.mean(np.sum(np.asarray(v,float)**2,axis=1))))

def _stage_a_rhs(x,gamma,core0,L0,require_native,mesh_rate,core_mode,mesh_method='segment_feedback',mesh_max_relative_rms=0.0):
    if core_mode=='fixed': cores=np.full(len(x),core0,float)
    elif core_mode=='global_volume': cores=uniform_global_volume_cores(x,core0,L0)
    else: raise ValueError(f'unknown stage_a_core_mode={core_mode}')
    up=velocity_from_cores(x,gamma,cores,require_native)
    um=tangential_redistribution_velocity(x,mesh_rate,mesh_method)
    cap=float(mesh_max_relative_rms or 0.0); pr=_rms(up); mr=_rms(um)
    if cap>0 and mr>cap*max(pr,1e-15): um*=cap*max(pr,1e-15)/max(mr,1e-30)
    return up+um,up,um,cores

def _rk4_stage_a(x,dt,gamma,core0,L0,require_native,mesh_rate,core_mode,mesh_method,mesh_max_relative_rms):
    f=lambda z:_stage_a_rhs(z,gamma,core0,L0,require_native,mesh_rate,core_mode,mesh_method,mesh_max_relative_rms)[0]
    k1=f(x); k2=f(x+.5*dt*k1); k3=f(x+.5*dt*k2); k4=f(x+dt*k3)
    return x+dt*(k1+2*k2+2*k3+k4)/6

def simulate_stage_a(x0,xref,cfg,out,mesh_rate_override=None):
    x=np.asarray(x0,float).copy(); xref=np.asarray(xref,float); gamma=float(cfg.get('gamma_dimensionless',1)); core0=float(cfg['core_fraction'])
    req=bool(cfg.get('require_native',True)); plan=integration_plan(xref,cfg,'stage_a_t_final'); steps=int(plan['steps']); dt=float(plan['dt']); stride=int(plan['stride'])
    mesh_rate=float(cfg.get('mesh_redistribution_rate',2.0) if mesh_rate_override is None else mesh_rate_override)
    mesh_method=str(cfg.get('mesh_redistribution_method','segment_feedback')); mesh_cap=float(cfg.get('mesh_max_relative_rms',0.0))
    core_mode=str(cfg.get('stage_a_core_mode','global_volume')); L0=float(np.sum(segment_lengths(x)))
    hard=float(cfg.get('stage_a_hard_ds_cv',0.45)); ts=[]; xs=[]; dscv=[]; coremean=[]; meshr=[]; physr=[]; stop_reason='COMPLETED'; completed_steps=steps
    for k in range(steps+1):
        if k%stride==0 or k==steps:
            ut,up,um,cores=_stage_a_rhs(x,gamma,core0,L0,req,mesh_rate,core_mode,mesh_method,mesh_cap); ds=segment_lengths(x); cv=float(ds.std()/max(ds.mean(),1e-30))
            ts.append(k*dt); xs.append(x.copy()); dscv.append(cv); coremean.append(float(np.mean(cores))); meshr.append(_rms(um)); physr.append(_rms(up))
            if cv>hard:
                stop_reason='HARD_MESH_QUALITY_STOP'; completed_steps=k; break
        if k<steps: x=_rk4_stage_a(x,dt,gamma,core0,L0,req,mesh_rate,core_mode,mesh_method,mesh_cap)
        if not np.isfinite(x).all(): raise FloatingPointError('non-finite geometry')
    np.savez_compressed(out,t=np.asarray(ts),x=np.asarray(xs),x_reference=xref,ds_cv=np.asarray(dscv),core_mean=np.asarray(coremean),mesh_speed_rms=np.asarray(meshr),physical_speed_rms=np.asarray(physr),dt=dt,dt_target=float(plan['dt_target']),steps=completed_steps,planned_steps=steps,stage_a_core_mode=core_mode,mesh_redistribution_rate=mesh_rate,mesh_redistribution_method=mesh_method,mesh_max_relative_rms=mesh_cap,backend=backend_name(),stop_reason=stop_reason)
    ratios=np.asarray(meshr)/np.maximum(np.asarray(physr),1e-15)
    return {'samples':len(ts),'steps':completed_steps,'planned_steps':steps,'dt':dt,'dt_target':float(plan['dt_target']),'actual_t_final':float(ts[-1]),'target_t_final':float(plan['t_final']),'max_ds_cv':float(max(dscv)),'max_mesh_to_physical_rms_ratio':float(np.max(ratios)) if len(ratios) else 0.0,'stop_reason':stop_reason,'stage_a_core_mode':core_mode,'mesh_redistribution_rate':mesh_rate,'mesh_redistribution_method':mesh_method,'backend':backend_name()}

def simulate_stage_b(x0,xref,ref_lengths,cfg,out,core_mode):
    x=np.asarray(x0,float).copy(); xref=np.asarray(xref,float); ref=np.asarray(ref_lengths,float); gamma=float(cfg.get('gamma_dimensionless',1)); core0=float(cfg['core_fraction']); exp=-.5 if core_mode=='material' else 0.0; req=bool(cfg.get('require_native',True))
    # Stage B is deliberately material-labelled: NO mesh redistribution.
    c=dict(cfg); c['t_final']=float(cfg.get('stage_b_t_final',4.0)); plan=integration_plan(xref,c,'t_final'); steps=int(plan['steps']); dt=float(plan['dt']); stride=int(plan['stride'])
    hard=float(cfg.get('stage_b_hard_ds_cv',0.45)); ts=[]; xs=[]; sig=[]; dscv=[]; corecv=[]; stop_reason='COMPLETED'; completed_steps=steps
    for k in range(steps+1):
        if k%stride==0 or k==steps:
            u,cores=velocity(x,gamma,core0,ref,exp,req); sr=stretch_rate(x,u); ds=segment_lengths(x); cv=float(ds.std()/max(ds.mean(),1e-30))
            ts.append(k*dt); xs.append(x.copy()); sig.append(sr.copy()); dscv.append(cv); corecv.append(float(cores.std()/max(cores.mean(),1e-30)))
            if cv>hard:
                stop_reason='HARD_MESH_QUALITY_STOP'; completed_steps=k; break
        if k<steps: x=rk4(x,dt,gamma,core0,ref,exp,req)
        if not np.isfinite(x).all(): raise FloatingPointError('non-finite geometry')
    np.savez_compressed(out,t=np.asarray(ts),x=np.asarray(xs),sigma=np.asarray(sig),x_reference=xref,reference_lengths=ref,ds_cv=np.asarray(dscv),core_cv=np.asarray(corecv),dt=dt,dt_target=float(plan['dt_target']),steps=completed_steps,planned_steps=steps,core_mode=core_mode,backend=backend_name(),stop_reason=stop_reason)
    return {'samples':len(ts),'steps':completed_steps,'planned_steps':steps,'dt':dt,'dt_target':float(plan['dt_target']),'actual_t_final':float(ts[-1]),'target_t_final':float(c['t_final']),'max_ds_cv':float(max(dscv)),'max_core_cv':float(max(corecv)),'stop_reason':stop_reason,'core_mode':core_mode,'backend':backend_name()}
