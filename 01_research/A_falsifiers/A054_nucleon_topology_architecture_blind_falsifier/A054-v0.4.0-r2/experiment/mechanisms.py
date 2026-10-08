from __future__ import annotations
import numpy as np
from .physics import tangents, remove_tangent, rms_field, velocity_components

def _core_force_one(i,comps,core,sigma_rep_core=1.5,sigma_attr_core=4.0,attraction_fraction=0.35):
    x=np.asarray(comps[i],float); F=np.zeros_like(x); sr=max(float(sigma_rep_core)*core,1e-9); sa=max(float(sigma_attr_core)*core,1e-9)
    for j,y in enumerate(comps):
        if j==i: continue
        y=np.asarray(y,float); d=x[:,None,:]-y[None,:,:]; r2=np.sum(d*d,axis=2)
        w=np.exp(-r2/(2*sr*sr))/(sr*sr)-float(attraction_fraction)*np.exp(-r2/(2*sa*sa))/(sa*sa)
        F += np.mean(w[:,:,None]*d,axis=1)
    return F

def core_shell_raw(comps,core,cfg):
    out=[]
    for i,c in enumerate(comps):
        F=_core_force_one(i,comps,core,**cfg); t=tangents(c); out.append(remove_tangent(c,np.cross(t,F)))
    return out

def elastic_raw(comps):
    out=[]
    for c in comps:
        c=np.asarray(c,float); ds=max(np.mean(np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1)),1e-12)
        lap=(np.roll(c,-1,axis=0)-2*c+np.roll(c,1,axis=0))/(ds*ds)
        bilap=(np.roll(lap,-1,axis=0)-2*lap+np.roll(lap,1,axis=0))/(ds*ds)
        force=-bilap; t=tangents(c); out.append(remove_tangent(c,np.cross(t,force)))
    return out

def make_context(comps,gammas,core,arm,gain,core_cfg):
    base=velocity_components(comps,gammas,core); v0=max(rms_field(base),1e-15); scales={}
    if arm in ('CORE','CORE_ELASTIC'):
        raw=core_shell_raw(comps,core,core_cfg); scales['CORE']=v0/max(rms_field(raw),1e-15)
    if arm in ('ELASTIC','CORE_ELASTIC'):
        raw=elastic_raw(comps); scales['ELASTIC']=v0/max(rms_field(raw),1e-15)
    return {'arm':arm,'gain':float(gain),'scales':scales,'v0':v0,'core_cfg':dict(core_cfg)}

def injected_velocity(comps,gammas,core,ctx):
    out=[v.copy() for v in velocity_components(comps,gammas,core)]; g=float(ctx['gain'])
    if ctx['arm'] in ('CORE','CORE_ELASTIC'):
        raw=core_shell_raw(comps,core,ctx['core_cfg']); s=ctx['scales']['CORE']; out=[a+g*s*b for a,b in zip(out,raw)]
    if ctx['arm'] in ('ELASTIC','CORE_ELASTIC'):
        raw=elastic_raw(comps); s=ctx['scales']['ELASTIC']; out=[a+g*s*b for a,b in zip(out,raw)]
    return [remove_tangent(c,v) for c,v in zip(comps,out)]
