from __future__ import annotations
import numpy as np
PI=np.pi

def polyline_stats(points,closed=True):
    p=np.asarray(points,float); q=np.roll(p,-1,axis=0) if closed else p[1:]; a=p if closed else p[:-1]; e=np.linalg.norm(q-a,axis=1)
    return {'n_vertices':len(p),'length':float(e.sum()),'edge_mean':float(e.mean()),'edge_min':float(e.min()),'edge_max':float(e.max()),'edge_cv':float(e.std()/max(e.mean(),1e-300)),'centroid':tuple(map(float,p.mean(axis=0)))}

def _segs(p):
    p=np.asarray(p,float); q=np.roll(p,-1,axis=0); return .5*(p+q),q-p

def interaction_energy(a,b,core_radius=0.0,threads=0):
    ma,da=_segs(a);mb,db=_segs(b); s=0.0;a2=core_radius**2
    for m,d in zip(ma,da):
        r=m[None,:]-mb; s+=np.sum((db@d)/np.sqrt(np.sum(r*r,axis=1)+a2))
    return float(s/(4*PI))

def interaction_force_gradient(a,b,core_radius=0.0,threads=0):
    ma,da=_segs(a);mb,db=_segs(b); f=np.zeros(3);a2=core_radius**2
    for m,d in zip(ma,da):
        r=m[None,:]-mb; den=(np.sum(r*r,axis=1)+a2)**1.5; f+=np.sum(r*((db@d)/den)[:,None],axis=0)
    return f/(4*PI)

def biot_savart(source,query,core_radius=0.0,threads=0):
    ms,ds=_segs(source);q=np.asarray(query,float);out=np.zeros_like(q);a2=core_radius**2
    for i,x in enumerate(q):
        r=x[None,:]-ms;den=(np.sum(r*r,axis=1)+a2)**1.5;out[i]=np.sum(np.cross(ds,r)/den[:,None],axis=0)/(4*PI)
    return out
