from __future__ import annotations
import numpy as np
try:
    from . import _native
    HAVE_NATIVE=True
except Exception:
    _native=None;HAVE_NATIVE=False

def backend_name(): return 'cpp-pybind11' if HAVE_NATIVE else 'numpy-reference'

def _segments(points,offsets,gammas):
    seg=[]
    for c in range(len(offsets)-1):
        a,b=int(offsets[c]),int(offsets[c+1]);x=points[a:b];y=np.roll(x,-1,axis=0)
        for j in range(len(x)): seg.append((c,j,0.5*(x[j]+y[j]),y[j]-x[j],gammas[c]))
    return seg

def field_velocity(samples,points,offsets,gammas,core):
    if HAVE_NATIVE:return _native.field_velocity(np.asarray(samples,float),np.asarray(points,float),np.asarray(offsets,np.int64),np.asarray(gammas,float),float(core))
    out=np.zeros_like(np.asarray(samples,float));a2=core*core
    for _,_,m,dl,g in _segments(points,offsets,gammas):
        r=samples-m;den=(np.sum(r*r,axis=1)+a2)**1.5;out+=g*np.cross(dl[None,:],r)/(4*np.pi*den[:,None])
    return out

def vortex_velocity(points,offsets,gammas,core,delta=0.615,c0=0.1395):
    if HAVE_NATIVE:return _native.vortex_velocity(np.asarray(points,float),np.asarray(offsets,np.int64),np.asarray(gammas,float),float(core),float(delta),float(c0))
    # Reference fallback: nonlocal regularized field at vertices + local curvature term.
    p=np.asarray(points,float);o=np.asarray(offsets,np.int64);g=np.asarray(gammas,float);out=field_velocity(p,p,o,g,core)
    for ci in range(len(g)):
        a,b=o[ci],o[ci+1];c=p[a:b];dm=c-np.roll(c,1,axis=0);dp=np.roll(c,-1,axis=0)-c
        lm=np.maximum(np.linalg.norm(dm,axis=1),1e-14);lp=np.maximum(np.linalg.norm(dp,axis=1),1e-14)
        t=dm/lm[:,None]+dp/lp[:,None];t/=np.maximum(np.linalg.norm(t,axis=1)[:,None],1e-14);ds=.5*(lm+lp)
        k=(np.roll(c,-1,axis=0)-2*c+np.roll(c,1,axis=0))/np.maximum(ds[:,None]**2,1e-14)
        Lam=np.log(np.maximum(2*np.sqrt(lm*lp)/(np.exp(delta)*core),1.0000001))+c0
        out[a:b]+=g[ci]*Lam[:,None]*np.cross(t,k)/(4*np.pi)
    return out

def min_nonlocal_segment_distance(points,offsets,adjacency=3):
    if HAVE_NATIVE:return float(_native.min_nonlocal_segment_distance(np.asarray(points,float),np.asarray(offsets,np.int64),int(adjacency)))
    # Conservative vertex fallback.
    p=np.asarray(points,float);o=np.asarray(offsets,np.int64);best=np.inf
    for ci in range(len(o)-1):
        a=p[o[ci]:o[ci+1]]
        for cj in range(ci,len(o)-1):
            b=p[o[cj]:o[cj+1]]
            for i,x in enumerate(a):
                for j,y in enumerate(b):
                    if ci==cj and min(abs(i-j),len(a)-abs(i-j))<=adjacency:continue
                    best=min(best,float(np.linalg.norm(x-y)))
    return best

def regularized_energy(points,offsets,gammas,core,rho=1.0):
    if HAVE_NATIVE:return float(_native.regularized_energy(np.asarray(points,float),np.asarray(offsets,np.int64),np.asarray(gammas,float),float(core),float(rho)))
    s=_segments(points,offsets,gammas);tot=0.
    for _,_,m1,d1,g1 in s:
        for _,_,m2,d2,g2 in s:tot+=g1*g2*np.dot(d1,d2)/np.sqrt(np.dot(m1-m2,m1-m2)+core*core)
    return rho*tot/(8*np.pi)
