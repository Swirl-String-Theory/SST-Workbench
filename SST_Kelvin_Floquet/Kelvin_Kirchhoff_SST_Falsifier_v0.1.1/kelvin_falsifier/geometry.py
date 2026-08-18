from __future__ import annotations
import math
import numpy as np


def closed_lengths(c):
    return np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1)

def curve_length(c): return float(np.sum(closed_lengths(c)))

def resample_closed(c,n):
    c=np.asarray(c,float); seg=closed_lengths(c); L=float(seg.sum())
    if L<=0: raise ValueError('zero curve length')
    s=np.r_[0,np.cumsum(seg)]
    ext=np.vstack([c,c[0]])
    tq=np.linspace(0,L,n,endpoint=False)
    out=np.empty((n,3),float)
    j=0
    for i,t in enumerate(tq):
        while j+1<len(s)-1 and s[j+1]<=t: j+=1
        h=s[j+1]-s[j]; a=0 if h==0 else (t-s[j])/h
        out[i]=(1-a)*ext[j]+a*ext[j+1]
    return out

def allocate_points(comps,total,min_per=48):
    C=len(comps); total=max(total,min_per*C)
    L=np.array([curve_length(c) for c in comps],float); raw=total*L/L.sum(); n=np.maximum(min_per,np.floor(raw).astype(int))
    while n.sum()<total: n[int(np.argmax(raw-n))]+=1
    while n.sum()>total:
        idx=np.where(n>min_per)[0]
        if len(idx)==0: break
        j=idx[int(np.argmax(n[idx]-raw[idx]))]; n[j]-=1
    return n.tolist()

def resample_components(comps,total,min_per=48):
    ns=allocate_points(comps,total,min_per); out=[resample_closed(c,n) for c,n in zip(comps,ns)]
    offsets=[0]
    for c in out: offsets.append(offsets[-1]+len(c))
    return out,np.vstack(out),offsets

def estimate_thickness(comps):
    # Conservative numerical fallback only; provenance gate marks this as estimated.
    edges=np.concatenate([closed_lengths(c) for c in comps])
    return float(8.0*np.median(edges))

def edge_cv(comps):
    e=np.concatenate([closed_lengths(c) for c in comps]); return float(np.std(e)/np.mean(e))

def _unit(v,eps=1e-15):
    n=np.linalg.norm(v,axis=-1,keepdims=True); return v/np.maximum(n,eps)

def tangents(c): return _unit(np.roll(c,-1,axis=0)-np.roll(c,1,axis=0))

def rodrigues(v,axis,angle):
    axis=np.asarray(axis,float); an=np.linalg.norm(axis)
    if an<1e-14: return v.copy()
    a=axis/an; return v*math.cos(angle)+np.cross(a,v)*math.sin(angle)+a*np.dot(a,v)*(1-math.cos(angle))

def parallel_frame(c):
    c=np.asarray(c,float); npt=len(c); t=tangents(c)
    axes=np.eye(3); a=axes[np.argmin(np.abs(axes@t[0]))]
    n=np.empty_like(c); n[0]=_unit(np.cross(t[0],a)[None,:])[0]
    for i in range(1,npt):
        cr=np.cross(t[i-1],t[i]); sn=np.linalg.norm(cr); cs=float(np.clip(np.dot(t[i-1],t[i]),-1,1))
        ni=n[i-1] if sn<1e-14 else rodrigues(n[i-1],cr,math.atan2(sn,cs))
        ni=ni-t[i]*np.dot(ni,t[i]); n[i]=ni/max(np.linalg.norm(ni),1e-15)
    # closure holonomy correction distributed by arclength
    cr=np.cross(t[-1],t[0]); sn=np.linalg.norm(cr); cs=float(np.clip(np.dot(t[-1],t[0]),-1,1))
    nc=n[-1] if sn<1e-14 else rodrigues(n[-1],cr,math.atan2(sn,cs))
    ang=math.atan2(float(np.dot(np.cross(nc,n[0]),t[0])),float(np.clip(np.dot(nc,n[0]),-1,1)))
    e=closed_lengths(c); s=np.r_[0,np.cumsum(e[:-1])]; L=e.sum()
    for i in range(npt): n[i]=rodrigues(n[i],t[i],ang*(s[i]/L))
    b=_unit(np.cross(t,n)); n=_unit(np.cross(b,t))
    return t,n,b

def frames_for_components(comps):
    T=[];N=[];B=[]
    for c in comps:
        t,n,b=parallel_frame(c); T.append(t);N.append(n);B.append(b)
    return np.vstack(T),np.vstack(N),np.vstack(B)

def rigid_fit(x,v):
    x=np.asarray(x,float); v=np.asarray(v,float); xc=x-x.mean(axis=0)
    A=np.zeros((3*len(x),6),float); y=v.reshape(-1)
    for i,(xx,yy,zz) in enumerate(xc):
        A[3*i+0]=[1,0,0,0,zz,-yy]
        A[3*i+1]=[0,1,0,-zz,0,xx]
        A[3*i+2]=[0,0,1,yy,-xx,0]
    p,*_=np.linalg.lstsq(A,y,rcond=None); pred=(A@p).reshape(-1,3)
    res=v-pred
    rms=lambda q: float(np.sqrt(np.mean(np.sum(q*q,axis=1))))
    return {'translation':p[:3],'omega':p[3:],'pred':pred,'residual':res,'relative_residual':rms(res)/max(rms(v),1e-30),'rms_velocity':rms(v)}

def rigid_basis(x):
    x=np.asarray(x,float); xc=x-x.mean(axis=0); N=len(x); cols=[]
    for a in np.eye(3): cols.append(np.tile(a,(N,1)).reshape(-1))
    for a in np.eye(3): cols.append(np.cross(np.tile(a,(N,1)),xc).reshape(-1))
    M=np.stack(cols,axis=1); q,_=np.linalg.qr(M); return q

def deformation_basis(comps, max_m, max_dim):
    offsets=[0]
    for c in comps: offsets.append(offsets[-1]+len(c))
    X=np.vstack(comps); _,NN,BB=frames_for_components(comps); C=len(comps)
    m_eff=max(1,min(max_m,max(1,int((max_dim/max(C,1)-2)//4))))
    raw=[]; meta=[]
    for ci,(lo,hi) in enumerate(zip(offsets[:-1],offsets[1:])):
        c=X[lo:hi]; e=closed_lengths(c); s=np.r_[0,np.cumsum(e[:-1])]; L=e.sum()
        for direction,label in [(NN,'n'),(BB,'b')]:
            z=np.zeros_like(X); z[lo:hi]=direction[lo:hi]; raw.append(z.reshape(-1)); meta.append((ci,0,label,'const'))
        for m in range(1,m_eff+1):
            ph=2*np.pi*m*s/L
            for direction,label in [(NN,'n'),(BB,'b')]:
                for trig,tlab in [(np.cos,'cos'),(np.sin,'sin')]:
                    z=np.zeros_like(X); z[lo:hi]=direction[lo:hi]*trig(ph)[:,None]; raw.append(z.reshape(-1)); meta.append((ci,m,label,tlab))
    R=np.stack(raw,axis=1)
    Qr=rigid_basis(X); R=R-Qr@(Qr.T@R)
    # rank-revealing SVD provides a stable orthonormal basis independent of raw ordering
    U,S,_=np.linalg.svd(R,full_matrices=False); tol=max(R.shape)*np.finfo(float).eps*(S[0] if len(S) else 1)
    rank=int(np.sum(S>tol)); rank=min(rank,max_dim)
    return U[:,:rank], {'raw_columns':len(raw),'rank':rank,'modes_per_component_used':m_eff,'raw_meta':meta}

def mode_k2(mode, comps):
    mode=np.asarray(mode); offsets=[0]
    for c in comps: offsets.append(offsets[-1]+len(c))
    num=0.0; den=0.0
    for c,lo,hi in zip(comps,offsets[:-1],offsets[1:]):
        phi=mode[lo:hi]; ds=curve_length(c)/len(c)
        der=(np.roll(phi,-1,axis=0)-np.roll(phi,1,axis=0))/(2*ds)
        num += float(np.sum(np.abs(der)**2)*ds); den += float(np.sum(np.abs(phi)**2)*ds)
    return num/max(den,1e-300)
