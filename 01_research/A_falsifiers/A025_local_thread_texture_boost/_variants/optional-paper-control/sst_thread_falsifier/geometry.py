from __future__ import annotations
import numpy as np


def component_lengths(points, offsets):
    p = np.asarray(points, float)
    out = []
    for a,b in zip(offsets[:-1], offsets[1:]):
        q = p[a:b]
        if len(q) < 2: out.append(0.0); continue
        out.append(float(np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1).sum()))
    return np.asarray(out)


def resample_closed_component(q, n):
    q = np.asarray(q, float)
    if len(q) >= 2 and np.linalg.norm(q[0]-q[-1]) < 1e-12 * max(1.0, np.ptp(q, axis=0).max()):
        q = q[:-1]
    if len(q) < 3:
        raise ValueError("component has fewer than 3 distinct points")
    nxt = np.roll(q,-1,axis=0)
    seg = np.linalg.norm(nxt-q,axis=1)
    if np.any(seg <= 0):
        keep = seg > 1e-14 * max(1.0, seg.max())
        q = q[keep]
        nxt = np.roll(q,-1,axis=0)
        seg = np.linalg.norm(nxt-q,axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    L = s[-1]
    targets = np.linspace(0.0, L, int(n), endpoint=False)
    out = np.empty((int(n),3), float)
    j=0
    for i,t in enumerate(targets):
        while j+1 < len(s) and s[j+1] <= t: j += 1
        k = j % len(q)
        u = 0.0 if seg[k] == 0 else (t-s[j])/seg[k]
        out[i] = (1-u)*q[k] + u*q[(k+1)%len(q)]
    return out


def resample_components(components, n_total):
    rawL = []
    for q in components:
        q=np.asarray(q,float)
        rawL.append(np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1).sum())
    rawL=np.asarray(rawL,float)
    if rawL.sum() <= 0: raise ValueError("zero total length")
    n_total=max(int(n_total),32*len(components))
    alloc=np.maximum(32,np.rint(n_total*rawL/rawL.sum()).astype(int))
    while alloc.sum() > n_total:
        i=int(np.argmax(alloc))
        if alloc[i] <= 32: break
        alloc[i]-=1
    while alloc.sum() < n_total:
        i=int(np.argmax(rawL/alloc))
        alloc[i]+=1
    res=[resample_closed_component(q,int(n)) for q,n in zip(components,alloc)]
    offsets=[0]
    for q in res: offsets.append(offsets[-1]+len(q))
    return np.vstack(res), np.asarray(offsets,dtype=np.int64)


def centroid(points):
    return np.mean(points,axis=0)


def gyration_tensor(points):
    x=np.asarray(points,float)-centroid(points)
    return (x.T@x)/len(x)


def radius_gyration(points):
    return float(np.sqrt(np.trace(gyration_tensor(points))))


def metrics(points, offsets):
    G=gyration_tensor(points)
    eig=np.linalg.eigvalsh(G)
    eig=np.maximum(eig,0.0)
    L=float(component_lengths(points,offsets).sum())
    rg=float(np.sqrt(eig.sum()))
    asph=0.0 if eig.sum()==0 else float(1.5*np.sum((eig-eig.mean())**2)/(eig.sum()**2))
    return {"length":L,"rg":rg,"gyration_eigenvalues":eig.tolist(),"asphericity":asph}


def kabsch_rms(a,b):
    A=np.asarray(a,float)-np.mean(a,axis=0)
    B=np.asarray(b,float)-np.mean(b,axis=0)
    H=A.T@B
    U,s,Vt=np.linalg.svd(H)
    R=U@Vt
    if np.linalg.det(R)<0:
        U[:,-1]*=-1
        R=U@Vt
    Ar=A@R
    return float(np.sqrt(np.mean(np.sum((Ar-B)**2,axis=1))))


def random_rotation(rng):
    M=rng.normal(size=(3,3))
    Q,R=np.linalg.qr(M)
    if np.linalg.det(Q)<0: Q[:,0]*=-1
    return Q


def characteristic_segment_length(points, offsets):
    """Minimum component-mean segment length for ds^2 time-step certification."""
    p=np.asarray(points,float); o=np.asarray(offsets,dtype=np.int64); vals=[]
    for lo,hi in zip(o[:-1],o[1:]):
        q=p[int(lo):int(hi)]
        if len(q)<3: continue
        ds=np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1)
        vals.append(float(np.mean(ds)))
    if not vals: raise ValueError("no valid component for characteristic segment length")
    return float(min(vals))
