from __future__ import annotations
import math
import numpy as np


def component_length(p: np.ndarray) -> float:
    q=np.roll(p,-1,axis=0)
    return float(np.linalg.norm(q-p,axis=1).sum())


def total_length(comps: list[np.ndarray]) -> float:
    return sum(component_length(c) for c in comps)


def resample_closed(p: np.ndarray, n: int) -> np.ndarray:
    p=np.asarray(p,float)
    q=np.vstack([p,p[0]])
    ds=np.linalg.norm(np.diff(q,axis=0),axis=1)
    s=np.concatenate([[0.0],np.cumsum(ds)])
    L=s[-1]
    if L<=0: raise ValueError("zero-length curve")
    target=np.linspace(0,L,n+1)[:-1]
    out=np.empty((n,3),float)
    for k in range(3): out[:,k]=np.interp(target,s,q[:,k])
    return out


def resample_components(comps: list[np.ndarray], n_per_component: int) -> list[np.ndarray]:
    return [resample_closed(c,n_per_component) for c in comps]


def pack_components(comps: list[np.ndarray]) -> tuple[np.ndarray,list[int]]:
    offsets=[0]
    for c in comps: offsets.append(offsets[-1]+len(c))
    return np.vstack(comps), offsets


def center_components(comps: list[np.ndarray]) -> list[np.ndarray]:
    allp=np.vstack(comps); ctr=allp.mean(axis=0)
    return [c-ctr for c in comps]


def edge_stats(comps: list[np.ndarray]) -> dict:
    e=[]
    for p in comps: e.extend(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1).tolist())
    a=np.asarray(e,float)
    return {"edge_mean":float(a.mean()),"edge_min":float(a.min()),"edge_max":float(a.max()),"edge_cv":float(a.std()/max(a.mean(),1e-300)),"edge_ratio":float(a.max()/max(a.min(),1e-300))}


def derivatives_closed(p: np.ndarray):
    n=len(p); L=component_length(p); ds=L/n
    d1=(np.roll(p,-1,axis=0)-np.roll(p,1,axis=0))/(2*ds)
    d2=(np.roll(p,-1,axis=0)-2*p+np.roll(p,1,axis=0))/(ds*ds)
    d3=(np.roll(p,-2,axis=0)-2*np.roll(p,-1,axis=0)+2*np.roll(p,1,axis=0)-np.roll(p,2,axis=0))/(2*ds**3)
    return d1,d2,d3,ds


def curvature_torsion(p: np.ndarray):
    d1,d2,d3,ds=derivatives_closed(p)
    cr=np.cross(d1,d2); cr2=np.sum(cr*cr,axis=1)
    speed=np.linalg.norm(d1,axis=1)
    kappa=np.linalg.norm(cr,axis=1)/np.maximum(speed**3,1e-300)
    tau=np.einsum("ij,ij->i",cr,d3)/np.maximum(cr2,1e-300)
    return kappa,tau,ds


def min_curvature_radius(comps: list[np.ndarray]) -> float:
    km=[]
    for p in comps:
        k,_,_=curvature_torsion(p); km.append(np.max(k))
    kmax=max(km)
    return float(1.0/kmax) if kmax>0 else float("inf")


def baseline_core_radius(dataset, comps: list[np.ndarray]) -> float:
    t=dataset.metrics.get("thickness")
    if isinstance(t,(int,float)) and t>0: return float(t)
    # Conservative fallback: curvature radius estimate, capped by coarse nonlocal vertex distance.
    rcur=min_curvature_radius(comps)
    p=np.vstack(comps)
    if len(p)>500: p=p[::max(1,len(p)//500)]
    dmin=float("inf")
    for i in range(len(p)):
        d=np.linalg.norm(p[i+1:]-p[i],axis=1)
        if len(d): dmin=min(dmin,float(d.min()))
    return max(1e-12,min(rcur,0.5*dmin if math.isfinite(dmin) else rcur))


def normalize_to_core(dataset, comps: list[np.ndarray]) -> tuple[list[np.ndarray],float]:
    a=baseline_core_radius(dataset,comps)
    centered=center_components(comps)
    return [c/a for c in centered],a


def rotation_minimizing_frame(p: np.ndarray) -> tuple[np.ndarray,np.ndarray,np.ndarray,float]:
    # Returns tangent, closed normal, binormal, and closure correction angle.
    n=len(p)
    d=np.roll(p,-1,axis=0)-np.roll(p,1,axis=0)
    t=d/np.maximum(np.linalg.norm(d,axis=1)[:,None],1e-300)
    ref=np.array([1.0,0.0,0.0])
    if abs(float(ref@t[0]))>0.85: ref=np.array([0.0,1.0,0.0])
    nvec=np.zeros_like(p); nvec[0]=ref-(ref@t[0])*t[0]; nvec[0]/=np.linalg.norm(nvec[0])
    for i in range(n-1):
        a=t[i]; b=t[i+1]; axis=np.cross(a,b); sn=np.linalg.norm(axis); cs=float(np.clip(a@b,-1,1))
        if sn<1e-14:
            v=nvec[i]
        else:
            k=axis/sn; ang=math.atan2(sn,cs); v=nvec[i]
            v=v*math.cos(ang)+np.cross(k,v)*math.sin(ang)+k*(k@v)*(1-math.cos(ang))
        v=v-(v@b)*b; v/=max(np.linalg.norm(v),1e-300); nvec[i+1]=v
    # Transport last normal across closing tangent step to t0, then measure mismatch.
    a=t[-1]; b=t[0]; axis=np.cross(a,b); sn=np.linalg.norm(axis); cs=float(np.clip(a@b,-1,1)); v=nvec[-1]
    if sn>=1e-14:
        k=axis/sn; ang=math.atan2(sn,cs)
        v=v*math.cos(ang)+np.cross(k,v)*math.sin(ang)+k*(k@v)*(1-math.cos(ang))
    v=v-(v@b)*b; v/=max(np.linalg.norm(v),1e-300)
    # signed angle v -> n0 about t0
    closure=math.atan2(float(t[0]@np.cross(v,nvec[0])),float(np.clip(v@nvec[0],-1,1)))
    # distribute correction so ribbon is periodic
    for i in range(n):
        ang=closure*(i/n)
        nn=nvec[i]; tt=t[i]
        nvec[i]=nn*math.cos(ang)+np.cross(tt,nn)*math.sin(ang)+tt*(tt@nn)*(1-math.cos(ang))
        nvec[i]/=max(np.linalg.norm(nvec[i]),1e-300)
    bvec=np.cross(t,nvec); bvec/=np.maximum(np.linalg.norm(bvec,axis=1)[:,None],1e-300)
    return t,nvec,bvec,closure


def ribbon_twist(p: np.ndarray, nvec: np.ndarray) -> float:
    # Discrete signed normal rotation around local tangent.
    d=np.roll(p,-1,axis=0)-p
    t=d/np.maximum(np.linalg.norm(d,axis=1)[:,None],1e-300)
    total=0.0
    for i in range(len(p)):
        j=(i+1)%len(p); axis=t[i]
        a=nvec[i]-(nvec[i]@axis)*axis
        b=nvec[j]-(nvec[j]@axis)*axis
        na=np.linalg.norm(a); nb=np.linalg.norm(b)
        if na<1e-12 or nb<1e-12: continue
        a/=na; b/=nb
        total += math.atan2(float(axis@np.cross(a,b)),float(np.clip(a@b,-1,1)))
    return total/(2*math.pi)


def smooth_periodic_vectors(v: np.ndarray, sigma_points: float) -> np.ndarray:
    n=len(v)
    if sigma_points<=0: return v.copy()
    half=max(1,int(math.ceil(4*sigma_points)))
    x=np.arange(-half,half+1)
    w=np.exp(-0.5*(x/sigma_points)**2); w/=w.sum()
    out=np.zeros_like(v)
    for k,ww in zip(x,w): out += ww*np.roll(v,k,axis=0)
    return out


def transverse_random_perturbation(p: np.ndarray, rms: float, sigma_s: float, rng: np.random.Generator) -> np.ndarray:
    L=component_length(p); ds=L/len(p); sigma_pts=max(sigma_s/ds,0.5)
    raw=rng.normal(size=p.shape); raw=smooth_periodic_vectors(raw,sigma_pts)
    t,_,_,_=rotation_minimizing_frame(p)
    raw=raw-np.sum(raw*t,axis=1)[:,None]*t
    rr=math.sqrt(float(np.mean(np.sum(raw*raw,axis=1))))
    if rr<=1e-15: return np.zeros_like(p)
    return raw*(rms/rr)


def fourier_normal_mode_perturbation(p: np.ndarray, mode: int, amplitude: float, phase: float=0.0, axis: str="normal") -> np.ndarray:
    _,n,b,_=rotation_minimizing_frame(p)
    frame=n if axis=="normal" else b
    theta=2*math.pi*mode*np.arange(len(p))/len(p)+phase
    return amplitude*np.cos(theta)[:,None]*frame


def dominant_curvature_mode(p: np.ndarray, max_mode: int=32) -> dict:
    k,_,_=curvature_torsion(p); x=k-k.mean(); spec=np.abs(np.fft.rfft(x))**2
    hi=min(max_mode,len(spec)-1)
    if hi<1: return {"mode":0,"power_fraction":0.0}
    j=1+int(np.argmax(spec[1:hi+1])); denom=float(spec[1:hi+1].sum())
    return {"mode":j,"power_fraction":float(spec[j]/denom) if denom>0 else 0.0}
