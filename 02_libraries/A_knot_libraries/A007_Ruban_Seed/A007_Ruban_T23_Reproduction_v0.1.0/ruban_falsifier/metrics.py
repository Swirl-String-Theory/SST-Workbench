"""Geometry-only diagnostics; none alone certifies Euler stability."""
import numpy as np
from scipy.spatial import cKDTree

def length(x):
    return float(np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1).sum())

def resample_closed_by_arclength(x, n=None):
    n=n or len(x)
    dx=np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1)
    s=np.r_[0,np.cumsum(dx)]
    if np.min(dx)<=1e-13: raise ValueError('degenerate segment')
    targets=np.linspace(0,s[-1],n,endpoint=False)
    return np.column_stack([np.interp(targets,s,np.r_[x[:,j],x[0,j]]) for j in range(3)])

def kabsch_rms(a,b):
    ac=a-a.mean(axis=0);bc=b-b.mean(axis=0)
    u,_,vt=np.linalg.svd(ac.T@bc)
    m=np.eye(3); m[-1,-1]=np.linalg.det(u@vt)
    rot=u@m@vt
    return float(np.sqrt(np.mean(np.sum((ac@rot-bc)**2,axis=1))))

def shape_drift(x,reference,quick=False):
    x=resample_closed_by_arclength(x); y=resample_closed_by_arclength(reference,len(x))
    # Circular shifts remove freedom in the material starting index.
    # Full cyclic matching at all snapshots is expensive, hence stride may
    # be chosen for diagnostics but not for scientific certification.
    shifts=range(0,len(x),max(1,len(x)//32 if quick else 1))
    return min(kabsch_rms(np.roll(x,k,axis=0),y) for k in shifts)

def segment_stats(x):
    ds=np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1)
    return {'min_ds':float(np.min(ds)),'max_ds':float(np.max(ds)),
            'ds_ratio':float(np.max(ds)/np.min(ds))}

def nonlocal_clearance(x,skip=4):
    # Nearest non-adjacent vertex distance, deliberately labeled vertex-only.
    tree=cKDTree(x)
    k=min(len(x),max(2*skip+7,16))
    dist,ind=tree.query(x,k=k)
    candidates=[]
    n=len(x)
    for i in range(n):
        valid=np.minimum(np.abs(ind[i]-i),n-np.abs(ind[i]-i))>skip
        if np.any(valid): candidates.append(float(np.min(dist[i,valid])))
    return float(min(candidates)) if candidates else None

def is_regular(x):
    return np.all(np.isfinite(x)) and np.all(np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1)>1e-9)
