"""Operator-split physical evolution + discrete uniform-arclength remap.

The physical RK4 RHS contains no tangential mesh controller.  Reparameterisation
is a discrete numerical operation at frozen physical times.  This separation is
the central v0.3.3 numerical experiment.
"""
from __future__ import annotations
import math
import numpy as np
from .solver import rk4,rhs,backend_name,stretch_rate
from .dynamics import plan
from .geometry import (segment_lengths,min_nonlocal_vertex_distance,resample_closed,
                       resample_closed_periodic_cubic,align_cyclic)


def _rms_points(d):
    d=np.asarray(d,float); return float(np.sqrt(np.mean(np.sum(d*d,axis=1))))


def _shape_distance(a,b,coarse_stride=4):
    aa=resample_closed(np.asarray(a,float),len(b)); bb=resample_closed(np.asarray(b,float),len(b))
    return float(align_cyclic(aa,bb,coarse_stride)[1])


def remap_event_times(T,interval):
    T=float(T); interval=float(interval)
    if not np.isfinite(interval) or interval<=0: return []
    # Endpoint remaps are excluded: a purely terminal interpolation should not
    # influence the measured final embedded curve.
    n=max(0,int(math.floor((T-1e-14)/interval)))
    return [float(j*interval) for j in range(1,n+1) if j*interval < T-1e-13]


def _remap_curve(x,cfg):
    kernel=str(cfg.get('operator_split_remap_kernel','periodic_cubic')).strip().lower()
    if kernel in ('periodic_cubic','periodic-cubic','cubic_periodic'):
        return resample_closed_periodic_cubic(
            x,len(x),
            oversample_factor=int(cfg.get('operator_split_remap_oversample_factor',16)),
            min_oversample=int(cfg.get('operator_split_remap_min_oversample',1024)))
    if kernel in ('legacy_linear','polygonal_linear'):
        return resample_closed(x,len(x))
    raise ValueError(f'UNKNOWN_OPERATOR_SPLIT_REMAP_KERNEL:{kernel}')


def simulate_operator_split(x0,cfg,T,mode='global_volume',*,remap_interval_override=None,
                            store_samples=None,dt_factor_override=None,max_ds_cv_override=None,
                            integration_plan=None,guard_stride_override=None):
    x=np.asarray(x0,float).copy(); ref=segment_lengths(x0); L0=float(np.sum(ref))
    gamma=float(cfg.get('gamma',1.0)); core0=float(cfg['core_fraction']); req=bool(cfg.get('require_native',True))
    steps,dt=plan(x,cfg,T,dt_factor_override=dt_factor_override) if integration_plan is None else integration_plan
    steps=int(steps); dt=float(dt)
    if steps<1 or steps>int(cfg.get('max_steps',300000)) or not np.isfinite(dt) or dt<=0 or not np.isclose(steps*dt,float(T),rtol=1e-12,atol=1e-12):
        raise ValueError('INVALID_FROZEN_INTEGRATION_PLAN')
    ns=int(store_samples or cfg.get('store_samples',96)); stride=max(1,int(math.ceil(steps/ns)))
    if guard_stride_override is not None: stride=max(1,int(guard_stride_override))
    hard_cv=float(cfg.get('operator_split_hard_ds_cv',cfg.get('long_hard_ds_cv',.45)) if max_ds_cv_override is None else max_ds_cv_override)
    interval=float(cfg.get('operator_split_remap_interval',.25) if remap_interval_override is None else remap_interval_override)
    events=remap_event_times(T,interval)
    evt=0; tol=max(1e-13,1e-11*max(1.0,float(T)))
    ts=[]; xs=[]; sig=[]; dscv=[]; gaps=[]; mesh_ratio=[]; physical_speed=[]
    remap_t=[]; remap_rms=[]; remap_shape=[]; remap_cv_before=[]; remap_cv_after=[]
    stop='COMPLETED'; actual=0.0
    def phys_step(z,h):
        return rk4(z,float(h),gamma,core0,mode,req,ref_lengths=ref,L0=L0)
    for k in range(steps+1):
        tgrid=float(k*dt)
        if k%stride==0 or k==steps:
            u,_=rhs(x,gamma,core0,mode,req,ref_lengths=ref,L0=L0)
            ds=segment_lengths(x); cv=float(ds.std()/max(ds.mean(),1e-15)); gap=float(min_nonlocal_vertex_distance(x,int(cfg.get('contact_skip',3)))/max(ds.mean(),1e-15))
            ts.append(tgrid); xs.append(x.copy()); sig.append(stretch_rate(x,u)); dscv.append(cv); gaps.append(gap); mesh_ratio.append(0.0); physical_speed.append(_rms_points(u)); actual=tgrid
            if cv>hard_cv: stop='MESH_QUALITY_STOP'; break
            if gap<float(cfg.get('min_gap_over_ds',.9)): stop='CONTACT_GUARD_STOP'; break
        if k==steps: break
        t0=tgrid; t1=float((k+1)*dt); cursor=t0
        while evt<len(events) and events[evt]<=t1+tol:
            te=events[evt]
            if te>cursor+tol: x=phys_step(x,te-cursor)
            before=x.copy(); ds0=segment_lengths(before); cv0=float(ds0.std()/max(ds0.mean(),1e-15))
            x=_remap_curve(before,cfg)
            ds1=segment_lengths(x); cv1=float(ds1.std()/max(ds1.mean(),1e-15))
            remap_t.append(float(te)); remap_rms.append(_rms_points(x-before)); remap_shape.append(_shape_distance(x,before,int(cfg.get('cyclic_stride',4)))); remap_cv_before.append(cv0); remap_cv_after.append(cv1)
            cursor=te; evt+=1
        if cursor<t1-tol: x=phys_step(x,t1-cursor)
        if not np.isfinite(x).all(): raise FloatingPointError('nonfinite geometry')
    return {'t':np.asarray(ts),'x':np.asarray(xs),'sigma':np.asarray(sig),'ds_cv':np.asarray(dscv),'gap_over_ds':np.asarray(gaps),
            'mesh_ratio':np.asarray(mesh_ratio),'mesh_speed_rms':np.zeros(len(ts),float),'physical_speed_rms':np.asarray(physical_speed),
            'dt':dt,'stop_reason':stop,'backend':backend_name(),'integration_steps':steps,'guard_stride':stride,
            'actual_t_final':float(actual),'target_t_final':float(T),'completed':bool(stop=='COMPLETED' and actual>=float(T)-max(1e-12,2*dt)),
            'mesh_redistribution_rate':0.0,'mesh_redistribution_method':'none','mesh_max_relative_rms':0.0,
            'reparameterization_scheme':('operator_split_periodic_cubic_arclength_v2' if str(cfg.get('operator_split_remap_kernel','periodic_cubic')).strip().lower() in ('periodic_cubic','periodic-cubic','cubic_periodic') else 'operator_split_legacy_polygonal_linear_arclength_diagnostic'),
            'remap_kernel':str(cfg.get('operator_split_remap_kernel','periodic_cubic')),'remap_interval':interval,
            'remap_event_times':np.asarray(remap_t),'remap_rms_displacement':np.asarray(remap_rms),'remap_shape_distance':np.asarray(remap_shape),
            'remap_ds_cv_before':np.asarray(remap_cv_before),'remap_ds_cv_after':np.asarray(remap_cv_after),'remap_event_count':int(len(remap_t))}
