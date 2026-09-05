from __future__ import annotations
import hashlib
import numpy as np

def read_xyz(path):
    rows=[]
    with open(path,'r',encoding='utf-8',errors='ignore') as f:
        for line in f:
            s=line.strip().replace(',',' ')
            if not s or s.startswith(('#','%',';')): continue
            vals=[]
            for t in s.split():
                try: vals.append(float(t))
                except ValueError: pass
            if len(vals)>=3: rows.append(vals[:3])
    x=np.asarray(rows,dtype=float)
    if x.ndim != 2 or len(x)<8:
        raise ValueError(f"Could not parse >=8 XYZ rows from {path}")
    scale=max(float(np.ptp(x,axis=0).max()),1.0)
    if np.linalg.norm(x[0]-x[-1]) < 1e-12*scale:
        x=x[:-1]
    return x

def write_xyz(path,x):
    np.savetxt(path,np.asarray(x,float),fmt="%.17g")

def center(x):
    x=np.asarray(x,float)
    return x-np.mean(x,axis=0,keepdims=True)

def resample_closed(x,n):
    x=center(x)
    seg=np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1)
    if np.any(seg<=0): raise ValueError("duplicate/zero-length segment")
    s=np.concatenate([[0.0],np.cumsum(seg)])
    xx=np.vstack([x,x[0]])
    st=np.linspace(0,s[-1],int(n),endpoint=False)
    y=np.column_stack([np.interp(st,s,xx[:,j]) for j in range(3)])
    return center(y)

def tangents(x):
    d=np.roll(x,-1,axis=0)-np.roll(x,1,axis=0)
    q=np.linalg.norm(d,axis=1)
    return d/np.maximum(q[:,None],1e-300)

def _rodrigues(v,axis,ang):
    axis=axis/max(float(np.linalg.norm(axis)),1e-300)
    return v*np.cos(ang)+np.cross(axis,v)*np.sin(ang)+axis*np.dot(axis,v)*(1-np.cos(ang))

def bishop_frame_closed(x):
    x=np.asarray(x,float)
    t=tangents(x); N=len(x)
    axes=np.eye(3)
    a=axes[np.argmin(np.abs(axes@t[0]))]
    n0=a-np.dot(a,t[0])*t[0]
    n0/=np.linalg.norm(n0)
    n=np.empty_like(x); n[0]=n0
    for i in range(1,N):
        c=np.clip(np.dot(t[i-1],t[i]),-1,1)
        ax=np.cross(t[i-1],t[i]); na=np.linalg.norm(ax)
        ni=n[i-1] if na<1e-12 else _rodrigues(n[i-1],ax/na,np.arctan2(na,c))
        ni-=np.dot(ni,t[i])*t[i]
        ni/=max(float(np.linalg.norm(ni)),1e-300)
        n[i]=ni
    c=np.clip(np.dot(t[-1],t[0]),-1,1)
    ax=np.cross(t[-1],t[0]); na=np.linalg.norm(ax)
    nend=n[-1] if na<1e-12 else _rodrigues(n[-1],ax/na,np.arctan2(na,c))
    nend-=np.dot(nend,t[0])*t[0]
    nend/=max(float(np.linalg.norm(nend)),1e-300)
    b0=np.cross(t[0],n[0])
    phi=np.arctan2(np.dot(nend,b0),np.dot(nend,n[0]))
    for i in range(N):
        n[i]=_rodrigues(n[i],t[i],-phi*i/N)
    b=np.cross(t,n)
    b/=np.maximum(np.linalg.norm(b,axis=1)[:,None],1e-300)
    return t,n,b

def min_nonlocal_clearance(x,samples=400,local_skip=5):
    """
    Fast numerical self-clearance on a dense arclength sampling.
    This is a numerical embedding-safety screen, not a formal knot proof.
    Local neighbours within +/- local_skip samples are excluded.
    """
    y=resample_closed(x,int(samples))
    diff=y[:,None,:]-y[None,:,:]
    d2=np.einsum('ijk,ijk->ij',diff,diff)
    N=len(y)
    idx=np.arange(N)
    sep=np.abs(idx[:,None]-idx[None,:])
    sep=np.minimum(sep,N-sep)
    d2[sep<=int(local_skip)]=np.inf
    return float(np.sqrt(np.min(d2)))

def hash_resampled(x,n):
    y=resample_closed(x,n)
    return hashlib.sha256(np.ascontiguousarray(y,dtype='<f8').tobytes()).hexdigest()

def kabsch_rms(a,b):
    a=center(a); b=center(b)
    H=b.T@a
    U,_,Vt=np.linalg.svd(H)
    R=U@Vt
    if np.linalg.det(R)<0:
        U[:,-1]*=-1; R=U@Vt
    br=b@R
    return float(np.sqrt(np.mean(np.sum((a-br)**2,axis=1))))

def curve_length(x):
    x=np.asarray(x,float)
    return float(np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1).sum())
