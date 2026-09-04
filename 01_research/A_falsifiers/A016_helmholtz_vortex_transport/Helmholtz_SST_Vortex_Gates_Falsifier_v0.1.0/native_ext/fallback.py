from __future__ import annotations
import numpy as np
PI=np.pi

def polyline_stats(points,closed=True):
    p=np.asarray(points,float); q=np.roll(p,-1,axis=0) if closed else p[1:]; a=p if closed else p[:-1]; e=np.linalg.norm(q-a,axis=1)
    return {'n_vertices':len(p),'length':float(e.sum()),'edge_mean':float(e.mean()),'edge_min':float(e.min()),'edge_max':float(e.max()),'edge_cv':float(e.std()/max(e.mean(),1e-300)),'centroid':tuple(map(float,p.mean(axis=0)))}

def _segs(p):
    p=np.asarray(p,float);q=np.roll(p,-1,axis=0);return p,q,.5*(p+q),q-p

def interaction_energy(a,b,core_radius=0.0,threads=0):
    _,_,ma,da=_segs(a);_,_,mb,db=_segs(b);a2=core_radius**2;s=0.0
    for m,d in zip(ma,da):
        r=m[None,:]-mb;s+=np.sum((db@d)/np.sqrt(np.sum(r*r,axis=1)+a2))
    return float(s/(4*PI))

def biot_savart(source,query,core_radius=0.0,kernel='softcore',threads=0):
    _,_,ms,ds=_segs(source);q=np.asarray(query,float);out=np.zeros_like(q);a=core_radius
    for i,x in enumerate(q):
        r=x[None,:]-ms;r2=np.sum(r*r,axis=1)
        if kernel=='softcore': den=(r2+a*a)**1.5
        elif kernel=='vatistas2': den=(r2*r2+a**4)**0.75
        else: den=np.maximum(np.sqrt(r2),1e-300)**3
        if a==0.0: den=np.where(r2<1e-28,np.inf,den)
        out[i]=np.sum(np.cross(ds,r)/den[:,None],axis=0)/(4*PI)
    return out

def gauss_linking(a,b,core_radius=0.0,threads=0):
    _,_,ma,da=_segs(a);_,_,mb,db=_segs(b);a2=core_radius**2;s=0.0
    for m,d in zip(ma,da):
        r=m[None,:]-mb;r2=np.sum(r*r,axis=1)+a2;den=np.where(r2<1e-28,np.inf,r2**1.5)
        s+=np.sum(np.einsum('ij,ij->i',np.cross(d[None,:],db),r)/den)
    return float(s/(4*PI))

def _segment_distance(p1,q1,p2,q2):
    # Robust-enough vector formula matching the C++ implementation.
    u=q1-p1;v=q2-p2;w=p1-p2;a=float(u@u);b=float(u@v);c=float(v@v);d=float(u@w);e=float(v@w);D=a*c-b*b;EPS=1e-14
    sD=D;tD=D
    if D<EPS:sN=0.0;sD=1.0;tN=e;tD=c
    else:
        sN=b*e-c*d;tN=a*e-b*d
        if sN<0:sN=0.0;tN=e;tD=c
        elif sN>sD:sN=sD;tN=e+b;tD=c
    if tN<0:
        tN=0.0
        if -d<0:sN=0.0
        elif -d>a:sN=sD
        else:sN=-d;sD=a
    elif tN>tD:
        tN=tD
        if (-d+b)<0:sN=0.0
        elif (-d+b)>a:sN=sD
        else:sN=(-d+b);sD=a
    sc=0.0 if abs(sN)<EPS else sN/sD;tc=0.0 if abs(tN)<EPS else tN/tD
    return float(np.linalg.norm(w+sc*u-tc*v))

def min_segment_distance(a,b,same_component=False,exclude_neighbors=2,threads=0):
    pa,qa,_,_=_segs(a);pb,qb,_,_=_segs(b);mn=np.inf;n=len(pa)
    for i in range(n):
        for j in range(len(pb)):
            if same_component:
                dij=abs(i-j);dij=min(dij,n-dij)
                if dij<=exclude_neighbors:continue
            mn=min(mn,_segment_distance(pa[i],qa[i],pb[j],qb[j]))
    return float(mn)


def doubly_critical_distance(a,b,same_component=False,exclude_neighbors=3,cos_tol=0.20,threads=0):
    _,_,ma,da=_segs(a);_,_,mb,db=_segs(b);na=np.linalg.norm(da,axis=1);nb=np.linalg.norm(db,axis=1);ta=da/np.maximum(na[:,None],1e-300);tb=db/np.maximum(nb[:,None],1e-300);mn=np.inf;n=len(ma)
    for i in range(n):
        r=mb-ma[i];d=np.linalg.norm(r,axis=1);ca=np.abs(r@ta[i])/np.maximum(d,1e-300);cb=np.abs(np.einsum('ij,ij->i',r,tb))/np.maximum(d,1e-300);mask=(d>1e-300)&(ca<=cos_tol)&(cb<=cos_tol)
        if same_component:
            idx=np.arange(len(mb));sep=np.abs(idx-i);sep=np.minimum(sep,n-sep);mask &= sep>exclude_neighbors
        if np.any(mask):mn=min(mn,float(np.min(d[mask])))
    return float(mn)
