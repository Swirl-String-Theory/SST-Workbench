from __future__ import annotations
import os, sys, time
from typing import Any
import numpy as np
from ._config import LOG_PREFIX

_BACKEND=None
_BACKEND_ERROR=None

def _load(force_python: bool=False, force_build: bool=False, verbose: bool=False):
    global _BACKEND,_BACKEND_ERROR
    if force_python:
        return None
    if _BACKEND is not None:
        return _BACKEND
    try:
        from .build_ext_if_needed import build_if_needed
        build_if_needed(force=force_build, verbose=verbose)
        from . import _native
        _BACKEND=_native
        return _BACKEND
    except Exception as exc:
        _BACKEND_ERROR=repr(exc)
        if verbose: print(f"{LOG_PREFIX} native backend unavailable: {exc}",file=sys.stderr)
        return None

def python_biot_savart_velocity(samples, seg_a, seg_b, gamma=1.0, core_radius=0.5, sample_chunk=64):
    """Pure NumPy reference. Midpoint segment kernel, matching C++ exactly."""
    samples=np.ascontiguousarray(samples,dtype=float); a=np.ascontiguousarray(seg_a,dtype=float); b=np.ascontiguousarray(seg_b,dtype=float)
    dl=b-a; mid=0.5*(a+b); eps2=float(core_radius)**2; pref=float(gamma)/(4.0*np.pi)
    out=np.empty((len(samples),3),dtype=float)
    for i0 in range(0,len(samples),int(sample_chunk)):
        s=samples[i0:i0+sample_chunk]
        r=s[:,None,:]-mid[None,:,:]
        den=(np.sum(r*r,axis=2)+eps2)**1.5
        c=np.cross(dl[None,:,:],r,axis=2)
        out[i0:i0+len(s)]=pref*np.sum(c/den[:,:,None],axis=1)
    return out

def biot_savart_velocity(samples, seg_a, seg_b, gamma=1.0, core_radius=0.5, threads=0, force_python=False, force_build=False, verbose=False):
    backend=_load(force_python=force_python,force_build=force_build,verbose=verbose)
    if backend is not None:
        t=time.perf_counter(); v=np.asarray(backend.biot_savart_velocity(np.asarray(samples,float),np.asarray(seg_a,float),np.asarray(seg_b,float),float(gamma),float(core_radius),int(threads)),float)
        return v,{"backend":"cpp","elapsed_s":time.perf_counter()-t,"build_info":dict(backend.build_info())}
    t=time.perf_counter(); v=python_biot_savart_velocity(samples,seg_a,seg_b,gamma,core_radius)
    return v,{"backend":"python","elapsed_s":time.perf_counter()-t,"build_error":_BACKEND_ERROR}

def backend_status(force_build=False,verbose=False)->dict[str,Any]:
    b=_load(force_python=False,force_build=force_build,verbose=verbose)
    if b is None: return {"backend":"python","native_available":False,"error":_BACKEND_ERROR}
    return {"backend":"cpp","native_available":True,"build_info":dict(b.build_info())}
