from pathlib import Path
import math,numpy as np
from .solver import rk4,rhs,backend_name,stretch_rate
from .geometry import segment_lengths,min_nonlocal_vertex_distance

def plan(x,cfg,T):
    ds=float(np.min(segment_lengths(x))); dt0=float(cfg.get('dt_factor',.02))*ds*ds/max(abs(float(cfg.get('gamma',1.0))),1e-15); steps=max(8,int(math.ceil(T/dt0))); mx=int(cfg.get('max_steps',300000))
    if steps>mx: raise RuntimeError(f'required_steps={steps} > max_steps={mx}; refusing dt coarsening')
    return steps,T/steps

def tangential_redistribution(x,rate=1.0):
    ds=segment_lengths(x); mean=float(np.mean(ds)); err=ds-mean; phi=np.r_[0,np.cumsum(err[:-1])]; phi-=phi.mean(); t=np.roll(x,-1,axis=0)-np.roll(x,1,axis=0); t/=np.maximum(np.linalg.norm(t,axis=1)[:,None],1e-15); return -float(rate)*phi[:,None]*t

def rk4_long(x,dt,gamma,core0,require_native,L0,mesh_rate):
    f=lambda z: rhs(z,gamma,core0,'global_volume',require_native,L0=L0)[0]+tangential_redistribution(z,mesh_rate)
    k1=f(x);k2=f(x+.5*dt*k1);k3=f(x+.5*dt*k2);k4=f(x+dt*k3);return x+dt*(k1+2*k2+2*k3+k4)/6

def simulate(x0,cfg,T,mode='fixed',long_mesh=False,perturb=None,store_samples=None):
    x=np.asarray(x0,float).copy(); ref=segment_lengths(x0); L0=float(np.sum(ref)); gamma=float(cfg.get('gamma',1.0)); core0=float(cfg['core_fraction']); req=bool(cfg.get('require_native',True)); steps,dt=plan(x,cfg,T); ns=int(store_samples or cfg.get('store_samples',96)); stride=max(1,int(math.ceil(steps/ns))); ts=[]; xs=[]; sig=[]; dscv=[]; gaps=[]; mesh_ratio=[]; stop='COMPLETED'
    for k in range(steps+1):
        if k%stride==0 or k==steps:
            u,c=rhs(x,gamma,core0,mode,req,ref_lengths=ref,L0=L0); ds=segment_lengths(x); ts.append(k*dt); xs.append(x.copy()); sig.append(stretch_rate(x,u)); dscv.append(float(ds.std()/max(ds.mean(),1e-15))); gaps.append(float(min_nonlocal_vertex_distance(x,int(cfg.get('contact_skip',3)))/max(ds.mean(),1e-15)))
            if long_mesh:
                um=tangential_redistribution(x,float(cfg.get('mesh_rate',1.5))); mesh_ratio.append(float(np.sqrt(np.mean(np.sum(um*um,axis=1)))/max(np.sqrt(np.mean(np.sum(u*u,axis=1))),1e-15)))
            else: mesh_ratio.append(0.0)
            if dscv[-1]>float(cfg.get('max_ds_cv',.35)): stop='MESH_QUALITY_STOP'; break
            if gaps[-1]<float(cfg.get('min_gap_over_ds',.9)): stop='CONTACT_GUARD_STOP'; break
        if k<steps:
            if long_mesh: x=rk4_long(x,dt,gamma,core0,req,L0,float(cfg.get('mesh_rate',1.5)))
            else: x=rk4(x,dt,gamma,core0,mode,req,ref_lengths=ref,L0=L0)
            if not np.isfinite(x).all(): raise FloatingPointError('nonfinite geometry')
    return {'t':np.asarray(ts),'x':np.asarray(xs),'sigma':np.asarray(sig),'ds_cv':np.asarray(dscv),'gap_over_ds':np.asarray(gaps),'mesh_ratio':np.asarray(mesh_ratio),'dt':dt,'stop_reason':stop,'backend':backend_name()}
