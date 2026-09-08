import math
import numpy as np
from .solver import rk4,rhs,backend_name,stretch_rate
from .geometry import segment_lengths,min_nonlocal_vertex_distance,tangents


def _rms(v):
    v=np.asarray(v,float)
    return float(np.sqrt(np.mean(np.sum(v*v,axis=1))))


def plan(x,cfg,T,dt_factor_override=None):
    ds=float(np.min(segment_lengths(x)))
    fac=float(cfg.get('dt_factor',.02) if dt_factor_override is None else dt_factor_override)
    dt0=fac*ds*ds/max(abs(float(cfg.get('gamma',1.0))),1e-15)
    steps=max(8,int(math.ceil(float(T)/dt0)))
    mx=int(cfg.get('max_steps',300000))
    if steps>mx:
        raise RuntimeError(f'required_steps={steps} > max_steps={mx}; refusing dt coarsening')
    return steps,float(T)/steps


def tangential_redistribution(x,rate=4.0,method='segment_feedback'):
    """Purely tangential numerical mesh-gauge velocity.

    The default segment-feedback controller solves
        alpha[i+1]-alpha[i] = -rate*(ell[i]-mean(ell))
    and applies u_mesh = alpha*t_hat.  The segment errors sum to zero,
    so the periodic compatibility condition is satisfied.
    """
    x=np.asarray(x,float)
    t=tangents(x)
    method=str(method)
    if method in ('none','off','mesh_off'):
        return np.zeros_like(x)
    if method in ('target_projection','arclength_target_projection'):
        from .geometry import resample_closed
        target=resample_closed(x,len(x)); d=target-x
        # Project the arclength-uniform target displacement onto the current tangent.
        # This is intentionally a tangential gauge controller: no normal component is added.
        return float(rate)*(np.sum(d*t,axis=1)[:,None]*t)
    if method!='segment_feedback':
        raise ValueError(f'unknown mesh_redistribution_method={method}')
    ds=segment_lengths(x); err=ds-float(np.mean(ds)); alpha=np.zeros(len(x),float)
    if len(x)>1:
        alpha[1:]=-float(rate)*np.cumsum(err[:-1])
    alpha-=float(np.mean(alpha))
    return alpha[:,None]*t


def _long_rhs(x,gamma,core0,require_native,L0,mesh_rate,mesh_method,mesh_cap):
    up,_=rhs(x,gamma,core0,'global_volume',require_native,L0=L0)
    um=tangential_redistribution(x,mesh_rate,mesh_method)
    pr=_rms(up); mr=_rms(um)
    cap=float(mesh_cap or 0.0)
    if cap>0.0 and mr>cap*max(pr,1e-15):
        um*=cap*max(pr,1e-15)/max(mr,1e-30)
    return up+um,up,um


def rk4_long(x,dt,gamma,core0,require_native,L0,mesh_rate,mesh_method,mesh_cap):
    f=lambda z:_long_rhs(z,gamma,core0,require_native,L0,mesh_rate,mesh_method,mesh_cap)[0]
    k1=f(x); k2=f(x+.5*dt*k1); k3=f(x+.5*dt*k2); k4=f(x+dt*k3)
    return x+dt*(k1+2*k2+2*k3+k4)/6


def simulate(x0,cfg,T,mode='fixed',long_mesh=False,perturb=None,store_samples=None,
             mesh_rate_override=None,dt_factor_override=None,max_ds_cv_override=None,
             integration_plan=None,guard_stride_override=None,mesh_method_override=None,
             mesh_cap_override=None):
    x=np.asarray(x0,float).copy(); ref=segment_lengths(x0); L0=float(np.sum(ref))
    gamma=float(cfg.get('gamma',1.0)); core0=float(cfg['core_fraction']); req=bool(cfg.get('require_native',True))
    steps,dt=plan(x,cfg,T,dt_factor_override=dt_factor_override) if integration_plan is None else integration_plan
    steps=int(steps); dt=float(dt)
    if steps<1 or steps>int(cfg.get('max_steps',300000)) or not np.isfinite(dt) or dt<=0 or not np.isclose(steps*dt,float(T),rtol=1e-12,atol=1e-12):
        raise ValueError('INVALID_FROZEN_INTEGRATION_PLAN')
    ns=int(store_samples or cfg.get('store_samples',96)); stride=max(1,int(math.ceil(steps/ns)))
    if guard_stride_override is not None: stride=max(1,int(guard_stride_override))
    mesh_rate=float(cfg.get('mesh_rate',4.0) if mesh_rate_override is None else mesh_rate_override)
    mesh_method=str(cfg.get('mesh_redistribution_method','segment_feedback') if mesh_method_override is None else mesh_method_override)
    mesh_cap=float(cfg.get('mesh_max_relative_rms',1.25) if mesh_cap_override is None else mesh_cap_override)
    hard_cv=float(cfg.get('max_ds_cv',.35) if max_ds_cv_override is None else max_ds_cv_override)
    ts=[]; xs=[]; sig=[]; dscv=[]; gaps=[]; mesh_ratio=[]; mesh_speed=[]; physical_speed=[]
    stop='COMPLETED'
    for k in range(steps+1):
        if k%stride==0 or k==steps:
            if long_mesh:
                _,u,um=_long_rhs(x,gamma,core0,req,L0,mesh_rate,mesh_method,mesh_cap)
                c=None
            else:
                u,c=rhs(x,gamma,core0,mode,req,ref_lengths=ref,L0=L0); um=np.zeros_like(u)
            ds=segment_lengths(x); ts.append(k*dt); xs.append(x.copy()); sig.append(stretch_rate(x,u))
            dscv.append(float(ds.std()/max(ds.mean(),1e-15)))
            gaps.append(float(min_nonlocal_vertex_distance(x,int(cfg.get('contact_skip',3)))/max(ds.mean(),1e-15)))
            pr=_rms(u); mr=_rms(um); physical_speed.append(pr); mesh_speed.append(mr); mesh_ratio.append(mr/max(pr,1e-15))
            if dscv[-1]>hard_cv:
                stop='MESH_QUALITY_STOP'; break
            if gaps[-1]<float(cfg.get('min_gap_over_ds',.9)):
                stop='CONTACT_GUARD_STOP'; break
        if k<steps:
            if long_mesh:
                x=rk4_long(x,dt,gamma,core0,req,L0,mesh_rate,mesh_method,mesh_cap)
            else:
                x=rk4(x,dt,gamma,core0,mode,req,ref_lengths=ref,L0=L0)
            if not np.isfinite(x).all():
                raise FloatingPointError('nonfinite geometry')
    actual=float(ts[-1]) if ts else 0.0
    return {
        't':np.asarray(ts),'x':np.asarray(xs),'sigma':np.asarray(sig),'ds_cv':np.asarray(dscv),
        'gap_over_ds':np.asarray(gaps),'mesh_ratio':np.asarray(mesh_ratio),'mesh_speed_rms':np.asarray(mesh_speed),
        'physical_speed_rms':np.asarray(physical_speed),'dt':dt,'stop_reason':stop,'backend':backend_name(),
        'integration_steps':steps,'guard_stride':stride,
        'actual_t_final':actual,'target_t_final':float(T),'completed':bool(stop=='COMPLETED' and actual>=float(T)-max(1e-12,2*dt)),
        'mesh_redistribution_rate':mesh_rate if long_mesh else 0.0,'mesh_redistribution_method':mesh_method if long_mesh else 'none',
        'mesh_max_relative_rms':mesh_cap if long_mesh else 0.0,
    }
