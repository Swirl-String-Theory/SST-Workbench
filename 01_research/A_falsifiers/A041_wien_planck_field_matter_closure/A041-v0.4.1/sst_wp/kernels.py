from __future__ import annotations
import math, numpy as np
from .native_ext import NATIVE_AVAILABLE, velocity as nv, energy_sum as ne

def velocity_python(points,offsets,gamma,core):
    P=np.asarray(points,float); V=np.zeros_like(P); pref=gamma/(4*math.pi)
    for ci in range(len(offsets)-1):
        a,b=int(offsets[ci]),int(offsets[ci+1]); C=P[a:b]
        Q=np.roll(C,-1,axis=0); dl=Q-C; mid=.5*(Q+C)
        for d,m in zip(dl,mid):
            r=P-m; den=(np.sum(r*r,axis=1)+core*core)**1.5; V += pref*np.cross(d,r)/den[:,None]
    return V

def energy_sum_python(points,offsets,core):
    mids=[];dls=[];P=np.asarray(points,float)
    for ci in range(len(offsets)-1):
        a,b=int(offsets[ci]),int(offsets[ci+1]);C=P[a:b];Q=np.roll(C,-1,axis=0);dls.append(Q-C);mids.append(.5*(Q+C))
    M=np.vstack(mids);D=np.vstack(dls); s=0.0
    # chunk to avoid huge temporary tensors
    for i in range(len(M)):
        r=M[i]-M; den=np.sqrt(np.sum(r*r,axis=1)+core*core); s += float(np.sum((D@D[i])/den))
    return s

def velocity(points,offsets,gamma,core,require_native=False):
    if NATIVE_AVAILABLE: return np.asarray(nv(points,np.asarray(offsets,dtype=np.int64),gamma,core))
    if require_native: raise RuntimeError('native backend required but not loaded')
    return velocity_python(points,offsets,gamma,core)
def energy_sum(points,offsets,core,require_native=False):
    if NATIVE_AVAILABLE: return float(ne(points,np.asarray(offsets,dtype=np.int64),core))
    if require_native: raise RuntimeError('native backend required but not loaded')
    return energy_sum_python(points,offsets,core)
