from __future__ import annotations
import numpy as np
from ..backend_contract import BackendResult

PI=3.141592653589793238462643383279502884

def vec_add(a,b): return np.asarray(a,dtype=np.float64)+np.asarray(b,dtype=np.float64)

def min_abs(x):
    x=np.asarray(x,dtype=np.float64).reshape(-1)
    return float(np.min(np.abs(x))) if len(x) else float("inf")

def biot_savart(points,queries,gamma=1.0,core=0.04,block=128):
    p=np.asarray(points,dtype=np.float64); q=np.asarray(queries,dtype=np.float64)
    if p.ndim!=2 or p.shape[1]!=3 or q.ndim!=2 or q.shape[1]!=3: raise ValueError("points/queries must be Nx3")
    if len(p)<3: raise ValueError("need >=3 closed filament points")
    if not np.isfinite(p).all() or not np.isfinite(q).all() or not np.isfinite([gamma,core]).all(): raise ValueError("non-finite input")
    if core<=0: raise ValueError("core must be > 0")
    nxt=np.roll(p,-1,axis=0); mids=.5*(p+nxt); dls=nxt-p; out=np.zeros_like(q)
    fac=float(gamma)/(4.0*PI); a2=float(core)**2
    for i0 in range(0,len(q),block):
        r=q[i0:i0+block,None,:]-mids[None,:,:]
        D=np.sum(r*r,axis=2)+a2
        out[i0:i0+block]=fac*np.sum(np.cross(dls[None,:,:],r)/(D*np.sqrt(D))[:,:,None],axis=1)
    return out

def result(metrics=None):
    return BackendResult("python","python-numpy-fp64","float64","REFERENCE",True,metrics or {})
