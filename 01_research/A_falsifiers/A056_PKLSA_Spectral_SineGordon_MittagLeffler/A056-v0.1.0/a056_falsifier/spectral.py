from __future__ import annotations
import numpy as np

def pod_metrics(phi, top_k=3):
    x=np.asarray(phi,float); x=x-np.mean(x,axis=0,keepdims=True)
    u,s,vh=np.linalg.svd(x,full_matrices=False)
    e=s*s; frac=e/max(np.sum(e),1e-30)
    # Only compare energetically resolved modes; noise-only singular vectors make
    # split-window subspace overlap meaningless.
    energetic=int(np.sum(frac > 1e-6))
    k=max(1,min(int(top_k),vh.shape[0],energetic if energetic>0 else 1))
    orth=float(np.linalg.norm(vh[:k]@vh[:k].T-np.eye(k),ord='fro'))
    mid=max(2,len(x)//2)
    def basis(xx):
        xx=xx-np.mean(xx,axis=0,keepdims=True)
        _,ss,v=np.linalg.svd(xx,full_matrices=False)
        kk=max(1,min(k,v.shape[0])); return ss,v[:kk]
    s1,v1=basis(x[:mid]); s2,v2=basis(x[mid:])
    kk=min(v1.shape[0],v2.shape[0])
    sv=np.linalg.svd(v1[:kk]@v2[:kk].T,compute_uv=False)
    overlap=float(np.mean(sv)) if len(sv) else 0.0
    q=x@vh[:k].T
    return {"top_energy_fraction":float(np.sum(frac[:k])),"orthogonality_residual":orth,"split_subspace_overlap":overlap,"rank":int(np.sum(s>max(s[0]*1e-12,1e-15))),"k":k}, q, vh[:k]

def derived_ringdown(t,q):
    q=np.asarray(q,float)
    e=np.sqrt(np.sum(q*q,axis=1)) if q.ndim==2 else np.abs(q)
    # mild deterministic smoothing, width 5, preserving endpoints by edge padding
    if len(e)>=7:
        ker=np.ones(5)/5; e=np.convolve(np.pad(e,(2,2),mode='edge'),ker,mode='valid')
    return np.asarray(t,float), e
