from __future__ import annotations
import numpy as np
try:
    from . import _fast
    HAVE_CPP=True
except Exception:
    _fast=None; HAVE_CPP=False

def _strip_duplicate(points):
    p=np.asarray(points,dtype=float)
    if p.ndim!=2 or p.shape[1]!=3: raise ValueError("points must be Nx3")
    if len(p)>=2:
        scale=max(float(np.linalg.norm(np.ptp(p,axis=0))),1e-300)
        if np.linalg.norm(p[0]-p[-1]) <= 1e-12*scale: p=p[:-1]
    if len(p)<8: raise ValueError("need >=8 unique points")
    return np.ascontiguousarray(p)

def closed_length_py(points):
    p=_strip_duplicate(points); return float(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1).sum())

def resample_closed_py(points,nout):
    p=_strip_duplicate(points); q=np.roll(p,-1,axis=0); seg=np.linalg.norm(q-p,axis=1)
    cum=np.concatenate([[0.0],np.cumsum(seg)]); L=cum[-1]
    snew=np.linspace(0.0,L,int(nout),endpoint=False)
    idx=np.searchsorted(cum,snew,side="right")-1; idx=np.clip(idx,0,len(p)-1)
    f=(snew-cum[idx])/np.maximum(seg[idx],1e-300)
    return p[idx]*(1-f[:,None])+q[idx]*f[:,None]

def curvature_radius_min_py(points):
    p=_strip_duplicate(points); n=len(p)
    a=np.roll(p,1,axis=0); b=p; c=np.roll(p,-1,axis=0)
    ab=b-a; bc=c-b; ac=c-a
    la=np.linalg.norm(ab,axis=1); lb=np.linalg.norm(bc,axis=1); lc=np.linalg.norm(ac,axis=1)
    area2=np.linalg.norm(np.cross(ab,bc),axis=1)
    kappa=2.0*area2/np.maximum(la*lb*lc,1e-300)
    good=kappa>1e-14/max(np.mean(la),1e-300)
    return float(np.min(1.0/kappa[good])) if np.any(good) else float("inf")

def estimate_thickness_py(points,exclude_steps=8):
    p=_strip_duplicate(points); n=len(p); local=curvature_radius_min_py(p); dmin=float("inf")
    tang=np.roll(p,-1,axis=0)-np.roll(p,1,axis=0); tang/=np.linalg.norm(tang,axis=1)[:,None]
    # Approximate doubly-critical self-distance: the chord is nearly perpendicular
    # to both local tangents. This avoids mistaking nearby along-curve points for rope contact.
    perp_tol=0.15
    for i in range(n):
        for j in range(i+1,n):
            sep=min(j-i,n-(j-i))
            if sep<=exclude_steps: continue
            r=p[j]-p[i]; d=float(np.linalg.norm(r))
            if not (d>0): continue
            if abs(float(np.dot(r,tang[i])))/d>perp_tol: continue
            if abs(float(np.dot(r,tang[j])))/d>perp_tol: continue
            if d<dmin: dmin=d
    nonlocal_r=0.5*dmin
    th=min(local,nonlocal_r)
    return {"thickness":float(th),"local_curvature_radius_min":float(local),"nonlocal_half_distance_min":float(nonlocal_r),"limiter":"curvature" if local<=nonlocal_r else "self_distance"}

def resample_closed(points,nout,require_cpp=False):
    if HAVE_CPP: return np.asarray(_fast.resample_closed(_strip_duplicate(points),int(nout)))
    if require_cpp: raise RuntimeError("C++ backend required but not loaded. Run run_build_cpp.cmd")
    return resample_closed_py(points,nout)

def estimate_thickness(points,exclude_steps=8,require_cpp=False):
    if HAVE_CPP: return dict(_fast.estimate_thickness(_strip_duplicate(points),int(exclude_steps)))
    if require_cpp: raise RuntimeError("C++ backend required but not loaded. Run run_build_cpp.cmd")
    return estimate_thickness_py(points,exclude_steps)

def field_velocity_gradient(points,queries,gamma=1.0,core_radius=1.0,require_cpp=False):
    p=_strip_duplicate(points); q=np.ascontiguousarray(np.asarray(queries,float))
    if q.ndim!=2 or q.shape[1]!=3: raise ValueError("queries must be Mx3")
    if HAVE_CPP:
        d=_fast.velocity_gradient(p,q,float(gamma),float(core_radius))
        return np.asarray(d["velocity"]),np.asarray(d["gradient"])
    if require_cpp: raise RuntimeError("C++ backend required but not loaded. Run run_build_cpp.cmd")
    return velocity_gradient_py(p,q,gamma,core_radius)

def velocity_gradient_py(points,queries,gamma=1.0,core_radius=1.0):
    p=_strip_duplicate(points); q=np.asarray(queries,float); n=len(p); m=len(q)
    nxt=np.roll(p,-1,axis=0); dl=nxt-p; mid=0.5*(p+nxt); C=float(gamma)/(4*np.pi)
    vel=np.zeros((m,3)); grad=np.zeros((m,3,3)); a2=float(core_radius)**2
    for s in range(n):
        r=q-mid[s]; D=np.sum(r*r,axis=1)+a2; inv3=D**-1.5; inv5=D**-2.5
        cross=np.cross(np.broadcast_to(dl[s],r.shape),r); vel += C*cross*inv3[:,None]
        for mm in range(3):
            em=np.zeros(3); em[mm]=1.0
            term=np.cross(dl[s],em)[None,:]*inv3[:,None] - 3.0*cross*r[:,mm,None]*inv5[:,None]
            grad[:,:,mm] += C*term
    return vel,grad

def cpp_info():
    if not HAVE_CPP: return {"loaded":False,"openmp_enabled":False,"openmp_max_threads":1}
    return {"loaded":True,"openmp_enabled":bool(getattr(_fast,"openmp_enabled",False)),"openmp_max_threads":int(getattr(_fast,"openmp_max_threads",1))}
