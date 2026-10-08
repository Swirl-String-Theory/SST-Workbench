from __future__ import annotations
import numpy as np

def induced_velocity_numpy(targets, components, gammas, core):
    targets=np.asarray(targets,float); out=np.zeros_like(targets); a2=float(core)**2
    for curve,gamma in zip(components,gammas):
        c=np.asarray(curve,float); q=np.roll(c,-1,axis=0); dl=q-c; mid=0.5*(c+q)
        # target x source x xyz
        r=targets[:,None,:]-mid[None,:,:]
        den=(np.sum(r*r,axis=2)+a2)**1.5
        out += float(gamma)/(4*np.pi)*np.sum(np.cross(dl[None,:,:],r)/den[:,:,None],axis=1)
    return out

def tangents(c):
    c=np.asarray(c,float); t=np.roll(c,-1,axis=0)-np.roll(c,1,axis=0); n=np.linalg.norm(t,axis=1); return t/np.maximum(n[:,None],1e-15)

def remove_tangent(c,v):
    t=tangents(c); return np.asarray(v,float)-np.einsum('ij,ij->i',v,t)[:,None]*t

def flatten(cs): return np.vstack([np.asarray(c,float) for c in cs])
def split(Y,sizes):
    out=[]; k=0
    for n in sizes: out.append(np.asarray(Y[k:k+n],float)); k+=n
    return out

def rms_field(fields):
    x=flatten(fields); return float(np.sqrt(np.mean(np.sum(x*x,axis=1))))

def velocity_components(comps,gammas,core):
    return [remove_tangent(c,induced_velocity_numpy(c,comps,gammas,core)) for c in comps]
