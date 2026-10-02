from __future__ import annotations
import sys,time
from typing import Any
import numpy as np
from ._config import LOG_PREFIX

_BACKEND=None; _BACKEND_ERROR=None

def _load(force_python=False,force_build=False,verbose=False):
    global _BACKEND,_BACKEND_ERROR
    if force_python:return None
    if _BACKEND is not None:return _BACKEND
    try:
        from .build_ext_if_needed import build_if_needed
        build_if_needed(force=force_build,verbose=verbose)
        from . import _native
        _BACKEND=_native; return _BACKEND
    except Exception as exc:
        _BACKEND_ERROR=repr(exc)
        if verbose: print(f'{LOG_PREFIX} native backend unavailable: {exc}',file=sys.stderr)
        return None

def python_biot_savart_velocity(samples,seg_a,seg_b,gamma=1.0,core_radius=0.5,sample_chunk=64):
    samples=np.ascontiguousarray(samples,float); a=np.ascontiguousarray(seg_a,float); b=np.ascontiguousarray(seg_b,float)
    dl=b-a; mid=.5*(a+b); eps2=float(core_radius)**2; pref=float(gamma)/(4*np.pi); out=np.empty((len(samples),3),float)
    for i0 in range(0,len(samples),int(sample_chunk)):
        s=samples[i0:i0+sample_chunk]; r=s[:,None,:]-mid[None,:,:]; den=(np.sum(r*r,axis=2)+eps2)**1.5
        out[i0:i0+len(s)]=pref*np.sum(np.cross(dl[None,:,:],r,axis=2)/den[:,:,None],axis=1)
    return out

def biot_savart_velocity(samples,seg_a,seg_b,gamma=1.0,core_radius=0.5,threads=0,force_python=False,force_build=False,verbose=False):
    b=_load(force_python,force_build,verbose)
    if b is not None:
        t=time.perf_counter(); v=np.asarray(b.biot_savart_velocity(np.asarray(samples,float),np.asarray(seg_a,float),np.asarray(seg_b,float),float(gamma),float(core_radius),int(threads)),float)
        return v,{'backend':'cpp','elapsed_s':time.perf_counter()-t,'build_info':dict(b.build_info())}
    t=time.perf_counter(); v=python_biot_savart_velocity(samples,seg_a,seg_b,gamma,core_radius)
    return v,{'backend':'python','elapsed_s':time.perf_counter()-t,'build_error':_BACKEND_ERROR}

def _segments(components):
    aa=[];bb=[]
    for c in components:
        c=np.asarray(c,float); aa.append(c); bb.append(np.roll(c,-1,axis=0))
    return np.ascontiguousarray(np.vstack(aa),float),np.ascontiguousarray(np.vstack(bb),float)

def python_circulation_from_segments(seg_a,seg_b,probe,gamma=1.0,core_radius=0.0):
    probe=np.asarray(probe,float); mid=.5*(probe+np.roll(probe,-1,axis=0)); dl=np.roll(probe,-1,axis=0)-probe
    u=python_biot_savart_velocity(mid,seg_a,seg_b,gamma,core_radius,sample_chunk=32)
    return float(np.sum(u*dl))

def circulation_from_centerlines(source_components,probe,gamma=1.0,core_radius=0.0,threads=0,force_python=False):
    a,b=_segments(source_components); p=np.ascontiguousarray(probe,float); n=_load(force_python=force_python,force_build=False,verbose=False)
    if n is not None and hasattr(n,'circulation_midpoint'):
        t=time.perf_counter(); q=float(n.circulation_midpoint(a,b,p,float(gamma),float(core_radius),int(threads)))
        return q,{'backend':'cpp','elapsed_s':time.perf_counter()-t,'build_info':dict(n.build_info())}
    t=time.perf_counter(); q=python_circulation_from_segments(a,b,p,gamma,core_radius)
    return q,{'backend':'python','elapsed_s':time.perf_counter()-t,'build_error':_BACKEND_ERROR}

def mutual_helicity_from_components(components,gammas=None,threads=0,force_python=False):
    comps=[np.asarray(c,float) for c in components]; gammas=list(gammas or [1.0]*len(comps)); total=0.0; back=[]
    # H_mutual = sum_i Gamma_i * integral_{Ki} u_{j!=i}.dl = 2 sum_{i<j} Gamma_i Gamma_j Lk_ij.
    for i,probe in enumerate(comps):
        for j,src in enumerate(comps):
            if i==j: continue
            q,info=circulation_from_centerlines([src],probe,gamma=float(gammas[j]),core_radius=0.0,threads=threads,force_python=force_python)
            total += float(gammas[i])*q; back.append(info.get('backend'))
    return float(total),{'backend':'cpp' if back and all(x=='cpp' for x in back) else 'python_or_mixed'}

def backend_status(force_build=False,verbose=False)->dict[str,Any]:
    b=_load(False,force_build,verbose)
    return {'backend':'python','native_available':False,'error':_BACKEND_ERROR} if b is None else {'backend':'cpp','native_available':True,'build_info':dict(b.build_info())}
