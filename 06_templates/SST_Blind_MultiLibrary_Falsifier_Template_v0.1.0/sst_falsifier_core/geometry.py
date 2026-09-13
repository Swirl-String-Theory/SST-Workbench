from __future__ import annotations
import numpy as np

def as_components(obj):
    if isinstance(obj,(list,tuple)):
        return [np.asarray(c,float) for c in obj]
    a=np.asarray(obj,float)
    if a.ndim==2 and a.shape[1]==3:return [a]
    if a.ndim==3 and a.shape[2]==3:return [a[i] for i in range(a.shape[0])]
    raise ValueError(f"unsupported geometry shape {a.shape}")

def uniform_resample_closed(points,n):
    p=np.asarray(points,float); q=np.vstack([p,p[0]])
    ds=np.linalg.norm(np.diff(q,axis=0),axis=1); s=np.r_[0,np.cumsum(ds)]
    if s[-1]<=0: raise ValueError("zero-length curve")
    target=np.linspace(0,s[-1],n+1)[:-1]
    out=np.column_stack([np.interp(target,s,q[:,k]) for k in range(3)])
    return out

def normalize_components(comps):
    comps=as_components(comps); allp=np.vstack(comps); c=allp.mean(axis=0); centered=[x-c for x in comps]
    rms=np.sqrt(np.mean(np.sum(np.vstack(centered)**2,axis=1)))
    if rms<=0: raise ValueError("zero RMS")
    return [x/rms for x in centered]

def segments(comps):
    mids=[]; dls=[]; targets=[]; tangents=[]; offsets=[]; total=0
    for c in as_components(comps):
        n=len(c); nxt=np.roll(c,-1,axis=0); prv=np.roll(c,1,axis=0)
        mids.append(.5*(c+nxt)); dls.append(nxt-c); targets.append(c)
        t=nxt-prv; t/=np.maximum(np.linalg.norm(t,axis=1,keepdims=True),1e-30); tangents.append(t)
        offsets.append((total,total+n)); total+=n
    return np.vstack(targets),np.vstack(mids),np.vstack(dls),np.vstack(tangents),offsets

def min_nonlocal_distance(points,skip=3):
    p=np.asarray(points,float); n=len(p); best=float('inf')
    for i in range(n):
        d=np.linalg.norm(p-p[i],axis=1); mask=np.ones(n,bool)
        for k in range(-skip,skip+1):mask[(i+k)%n]=False
        if np.any(mask):best=min(best,float(np.min(d[mask])))
    return best
