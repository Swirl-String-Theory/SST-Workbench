"""Dimensionless closed-polyline geometry diagnostics; no SST constants."""
from __future__ import annotations
import io
import numpy as np

def parse_xyz(raw):
    text=raw.decode('utf-8-sig') if isinstance(raw,bytes) else raw
    blocks=[]; cur=[]
    for line in text.splitlines()+['']:
        s=line.strip()
        if not s:
            if cur: blocks.append(np.asarray(cur,float));cur=[]
            continue
        if s.startswith('#'):continue
        values=s.split()
        if len(values)!=3:raise ValueError('XYZ rows require three columns')
        cur.append([float(v) for v in values])
    if any(len(x)<8 for x in blocks):raise ValueError('component fewer than 8 points')
    if any(not np.isfinite(x).all() for x in blocks):raise ValueError('nonfinite XYZ')
    return blocks

def arclength_resample(X,n):
    if n<12:raise ValueError('Need >=12 points')
    X=np.asarray(X,float)
    ds=np.linalg.norm(np.roll(X,-1,axis=0)-X,axis=1)
    if np.min(ds)<=0:raise ValueError('repeated vertices')
    s=np.r_[0.,np.cumsum(ds)]
    q=np.linspace(0,s[-1],n,endpoint=False)
    closed=np.vstack([X,X[0]])
    return np.column_stack([np.interp(q,s,closed[:,k]) for k in range(3)])

def normalized(components):
    X=np.concatenate(components)
    center=X.mean(0)
    radius=float(np.sqrt(np.mean(np.sum((X-center)**2,axis=1))))
    if radius<=0: raise ValueError('degenerate scale')
    return [(p-center)/radius for p in components], dict(center=center.tolist(),L0_source_units=radius)

def perimeter(X):return float(np.linalg.norm(np.roll(X,-1,axis=0)-X,axis=1).sum())

def q_curvature(X):
    """Dimensionless L0^2/L integral kappa^2 ds, with L0=1."""
    E=np.roll(X,-1,axis=0)-X
    ds=np.linalg.norm(E,axis=1)
    t=E/ds[:,None]
    t_prev=np.roll(t,1,axis=0)
    local_ds=(ds+np.roll(ds,1))/2
    k2=np.sum((t-t_prev)**2,axis=1)/local_ds**2
    return float(np.sum(k2*local_ds)/np.sum(ds))

def shape_error(X,X0):
    """Optimal proper rigid rotation/translation, without allowing reflections."""
    a=X-X.mean(0);b=X0-X0.mean(0)
    u,_,vt=np.linalg.svd(a.T@b)
    D=np.diag([1.,1.,np.linalg.det(u@vt)])
    rotated=a@u@D@vt
    return float(np.linalg.norm(rotated-b)/max(np.linalg.norm(b),1.e-20))

def pair_linking(A,B):
    """Finite-segment midpoint Gauss integral. Diagnostic, not topology proof."""
    ea=np.roll(A,-1,axis=0)-A;eb=np.roll(B,-1,axis=0)-B
    ma=(A+np.roll(A,-1,axis=0))/2;mb=(B+np.roll(B,-1,axis=0))/2
    r=ma[:,None,:]-mb[None,:,:]
    cross=np.cross(ea[:,None,:],eb[None,:,:])
    denom=np.linalg.norm(r,axis=-1)**3
    if np.min(denom)<1e-20:return float('nan')
    return float(np.sum(np.sum(cross*r,axis=-1)/denom)/(4*np.pi))

def point_clearance(A,B):
    """Vertex proxy only, not certified segment-segment minimum."""
    return float(np.sqrt(np.min(np.sum((A[:,None,:]-B[None,:,:])**2,axis=-1))))

def self_clearance_proxy(A):
    n=len(A);diff=A[:,None,:]-A[None,:,:]
    D=np.sum(diff**2,axis=-1)
    idx=np.arange(n)
    gap=np.minimum(np.abs(idx[:,None]-idx[None,:]),n-np.abs(idx[:,None]-idx[None,:]))
    D[gap<=3]=np.inf
    return float(np.sqrt(np.min(D)))

def perturb_shape(X, eps):
    """Predefined position-dependent, zero-mean shape perturbation."""
    Xc=X-X.mean(0); t=np.arange(len(X))*2*np.pi/len(X)
    envelope=(np.cos(2*t)+0.5*np.sin(3*t))[:,None]
    vec=Xc*envelope;vec-=vec.mean(0)
    m=np.sqrt(np.mean(np.sum(vec**2,axis=1)))
    if m<=1e-12:raise ValueError('degenerate perturbation')
    return X+eps*vec/m
