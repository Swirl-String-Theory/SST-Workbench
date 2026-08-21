from __future__ import annotations
import numpy as np

def read_xyz(path):
    rows=[]
    with open(path,'r',encoding='utf-8',errors='ignore') as f:
        for line in f:
            s=line.strip().replace(',',' ')
            if not s or s.startswith(('#','%',';')): continue
            toks=s.split()
            vals=[]
            for t in toks:
                try: vals.append(float(t))
                except ValueError: pass
            if len(vals)>=3: rows.append(vals[:3])
    x=np.asarray(rows,float)
    if x.ndim!=2 or x.shape[0]<8: raise ValueError(f"could not parse >=8 XYZ rows from {path}")
    if np.linalg.norm(x[0]-x[-1]) < 1e-12*np.ptp(x,axis=0).max(): x=x[:-1]
    return x

def center(x): return np.asarray(x,float)-np.mean(x,axis=0,keepdims=True)

def length(x):
    return float(np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1).sum())

def resample_closed(x,n):
    x=center(x); seg=np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1)
    if np.any(seg<=0): raise ValueError("duplicate/zero-length segment")
    s=np.concatenate([[0.0],np.cumsum(seg)]); L=s[-1]
    xx=np.vstack([x,x[0]])
    st=np.linspace(0,L,n,endpoint=False)
    out=np.column_stack([np.interp(st,s,xx[:,j]) for j in range(3)])
    return center(out)

def tangents(x):
    d=np.roll(x,-1,axis=0)-np.roll(x,1,axis=0); q=np.linalg.norm(d,axis=1)
    return d/np.maximum(q[:,None],1e-300)

def _rodrigues(v,axis,ang):
    axis=axis/max(np.linalg.norm(axis),1e-300)
    return v*np.cos(ang)+np.cross(axis,v)*np.sin(ang)+axis*np.dot(axis,v)*(1-np.cos(ang))

def bishop_frame_closed(x):
    t=tangents(x); npts=len(x)
    axes=np.eye(3); a=axes[np.argmin(np.abs(axes@t[0]))]
    n0=a-np.dot(a,t[0])*t[0]; n0/=np.linalg.norm(n0)
    n=np.empty_like(x); n[0]=n0
    for i in range(1,npts):
        c=np.clip(np.dot(t[i-1],t[i]),-1,1); ax=np.cross(t[i-1],t[i]); na=np.linalg.norm(ax)
        ni=n[i-1] if na<1e-12 else _rodrigues(n[i-1],ax/na,np.arctan2(na,c))
        ni-=np.dot(ni,t[i])*t[i]; ni/=max(np.linalg.norm(ni),1e-300); n[i]=ni
    # holonomy closure correction: transport last normal across seam to t0
    c=np.clip(np.dot(t[-1],t[0]),-1,1); ax=np.cross(t[-1],t[0]); na=np.linalg.norm(ax)
    nend=n[-1] if na<1e-12 else _rodrigues(n[-1],ax/na,np.arctan2(na,c))
    nend-=np.dot(nend,t[0])*t[0]; nend/=max(np.linalg.norm(nend),1e-300)
    b0=np.cross(t[0],n[0]); phi=np.arctan2(np.dot(nend,b0),np.dot(nend,n[0]))
    for i in range(npts): n[i]=_rodrigues(n[i],t[i],-phi*i/npts)
    b=np.cross(t,n); b/=np.maximum(np.linalg.norm(b,axis=1)[:,None],1e-300)
    return t,n,b

def modal_basis(x,m):
    _,n,b=bishop_frame_closed(x); N=len(x); th=2*np.pi*m*np.arange(N)/N
    raw=[np.cos(th)[:,None]*n,np.sin(th)[:,None]*n,np.cos(th)[:,None]*b,np.sin(th)[:,None]*b]
    A=np.stack([r.reshape(-1) for r in raw],axis=1)
    Q,_=np.linalg.qr(A)
    out=[Q[:,j].reshape(N,3) for j in range(4)]
    # normalize each to unit RMS point displacement, not unit flattened norm
    return [e/np.sqrt(np.mean(np.sum(e*e,axis=1))) for e in out]

def kabsch_rms(a,b):
    a=center(a); b=center(b); H=b.T@a; U,_,Vt=np.linalg.svd(H); R=U@Vt
    if np.linalg.det(R)<0: U[:,-1]*=-1; R=U@Vt
    br=b@R
    return float(np.sqrt(np.mean(np.sum((a-br)**2,axis=1))))
