from __future__ import annotations
import importlib
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
        import _a056_native as n
        return np.asarray(n.softened_velocity(targets,mids,dls,float(gamma),float(core)))
    except Exception:
        return None


def available_backends():
    out={"python_fp64":True,"cpp_fp64":False,"sycl_worker":False}
    try:
        import _a056_native; out["cpp_fp64"]=True
    except Exception: pass
    return out


def velocity(targets,mids,dls,gamma=1.0,core=.03,backend="python"):
    if backend in {"python","python_fp64","cpu"}:
        return _numpy_velocity(targets,mids,dls,gamma,core),"python-fp64"
    if backend in {"native","cpp","cpp_fp64"}:
        out=_native_velocity(targets,mids,dls,gamma,core)
        if out is None: raise RuntimeError("native backend unavailable")
        return out,"cpp-fp64"
    raise ValueError(f"unknown backend: {backend}")


def parity(targets,mids,dls,gamma=1.0,core=.03):
    ref,_=velocity(targets,mids,dls,gamma,core,"python")
    cand=_native_velocity(targets,mids,dls,gamma,core)
    if cand is None:
        return {"available":False,"relative_l2":None,"max_abs":None}
    return {
      "available":True,
      "relative_l2":float(np.linalg.norm(cand-ref)/max(np.linalg.norm(ref),1e-30)),
      "max_abs":float(np.max(np.abs(cand-ref))),
      "reference_norm":float(np.linalg.norm(ref)),
      "candidate_norm":float(np.linalg.norm(cand)),
    }
