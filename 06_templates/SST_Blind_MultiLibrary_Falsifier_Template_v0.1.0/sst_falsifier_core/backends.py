from __future__ import annotations
import importlib, os
import numpy as np

def _numpy_velocity(targets,mids,dls,gamma,core,block=128):
    t=np.asarray(targets,float); m=np.asarray(mids,float); dl=np.asarray(dls,float); out=np.zeros_like(t)
    fac=float(gamma)/(4*np.pi); a2=float(core)**2
    for i0 in range(0,len(t),block):
        x=t[i0:i0+block,None,:]-m[None,:,:]
        den=np.power(np.sum(x*x,axis=2)+a2,1.5)
        cross=np.cross(dl[None,:,:],x)
        out[i0:i0+block]=fac*np.sum(cross/den[:,:,None],axis=1)
    return out

def _native_velocity(targets,mids,dls,gamma,core):
    try:
        import _sst_falsifier_native as n
        return np.asarray(n.softened_velocity(targets,mids,dls,float(gamma),float(core)))
    except Exception:
        return _numpy_velocity(targets,mids,dls,gamma,core)

def _cupy_velocity(targets,mids,dls,gamma,core):
    import cupy as cp
    t=cp.asarray(targets,dtype=cp.float64); m=cp.asarray(mids,dtype=cp.float64); dl=cp.asarray(dls,dtype=cp.float64)
    x=t[:,None,:]-m[None,:,:]; den=cp.power(cp.sum(x*x,axis=2)+float(core)**2,1.5)
    v=(float(gamma)/(4*cp.pi))*cp.sum(cp.cross(dl[None,:,:],x)/den[:,:,None],axis=1)
    return cp.asnumpy(v)

def _dpnp_velocity(targets,mids,dls,gamma,core):
    import dpnp as xp
    t=xp.asarray(targets,dtype=xp.float64); m=xp.asarray(mids,dtype=xp.float64); dl=xp.asarray(dls,dtype=xp.float64)
    x=t[:,None,:]-m[None,:,:]; den=xp.power(xp.sum(x*x,axis=2)+float(core)**2,1.5)
    # dpnp.cross availability varies; explicit cross is safer
    a=dl[None,:,:]; cr=xp.stack([a[:,:,1]*x[:,:,2]-a[:,:,2]*x[:,:,1], a[:,:,2]*x[:,:,0]-a[:,:,0]*x[:,:,2], a[:,:,0]*x[:,:,1]-a[:,:,1]*x[:,:,0]],axis=2)
    v=(float(gamma)/(4*np.pi))*xp.sum(cr/den[:,:,None],axis=1)
    return xp.asnumpy(v)

def available_backends():
    out={"cpu":True,"python":True,"cupy":False,"dpnp":False}
    for m,k in [("cupy","cupy"),("dpnp","dpnp")]:
        try: importlib.import_module(m); out[k]=True
        except Exception: pass
    try:
        import _sst_falsifier_native; out["native"]=True
    except Exception: out["native"]=False
    return out

def velocity(targets,mids,dls,gamma=1.0,core=.03,backend="auto"):
    av=available_backends(); requested=backend or "auto"
    if requested=="auto":
        requested="dpnp" if av["dpnp"] else ("cupy" if av["cupy"] else ("native" if av["native"] else "cpu"))
    if requested in {"cpu","native"}: return _native_velocity(targets,mids,dls,gamma,core),"native" if av["native"] else "numpy"
    if requested=="python": return _numpy_velocity(targets,mids,dls,gamma,core),"numpy"
    if requested=="cupy": return _cupy_velocity(targets,mids,dls,gamma,core),"cupy"
    if requested in {"dpnp","sycl"}: return _dpnp_velocity(targets,mids,dls,gamma,core),"dpnp"
    raise ValueError(f"unknown/unavailable backend {requested}")

def parity(targets,mids,dls,gamma=1.0,core=.03,gpu_backend="auto"):
    ref,_=velocity(targets,mids,dls,gamma,core,"cpu")
    cand,name=velocity(targets,mids,dls,gamma,core,gpu_backend)
    err=float(np.linalg.norm(cand-ref)/max(np.linalg.norm(ref),1e-30))
    return {"backend":name,"relative_l2":err,"cpu_norm":float(np.linalg.norm(ref)),"candidate_norm":float(np.linalg.norm(cand))}
