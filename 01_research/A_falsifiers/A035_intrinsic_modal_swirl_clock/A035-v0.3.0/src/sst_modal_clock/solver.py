import numpy as np
from .geometry import next_prev_indices, normalize_offsets
try:
    from . import _native
    HAVE_NATIVE=True
except Exception:
    _native=None; HAVE_NATIVE=False

def _next_index(n,component_offsets=None): return next_prev_indices(int(n),component_offsets)[0]

def segment_lengths(x,component_offsets=None):
    x=np.asarray(x,float); nxt=_next_index(len(x),component_offsets); return np.linalg.norm(x[nxt]-x,axis=1)

def segment_cores(x,ref,core0,exp,component_offsets=None):
    return float(core0)*np.power(np.maximum(segment_lengths(x,component_offsets),1e-15)/np.maximum(ref,1e-15),float(exp))

def velocity_py(x,gamma,cores,component_offsets=None):
    x=np.asarray(x,float);cores=np.asarray(cores,float);n=len(x);u=np.zeros_like(x);pref=gamma/(4*np.pi);nxt=_next_index(n,component_offsets)
    for j in range(n):
        k=int(nxt[j]);seg=x[k]-x[j];mid=.5*(x[j]+x[k]);r=x-mid;cr=np.cross(np.broadcast_to(seg,r.shape),r);den=(np.sum(r*r,axis=1)+cores[j]**2)**1.5;u+=pref*cr/den[:,None]
    return u

def velocity_from_cores(x,gamma,cores,require_native=False,component_offsets=None):
    x=np.asarray(x,float);cores=np.asarray(cores,float);nxt=_next_index(len(x),component_offsets)
    if HAVE_NATIVE:
        if hasattr(_native,'velocity_variable_core_indexed'):
            return np.asarray(_native.velocity_variable_core_indexed(np.ascontiguousarray(x,float),float(gamma),np.ascontiguousarray(cores,float),np.ascontiguousarray(nxt,np.int64)))
        if len(normalize_offsets(component_offsets,len(x)))==2:
            return np.asarray(_native.velocity_variable_core(np.ascontiguousarray(x,float),float(gamma),np.ascontiguousarray(cores,float)))
    if require_native: raise RuntimeError('Native indexed extension unavailable; run run_build_native.cmd')
    return velocity_py(x,gamma,cores,component_offsets)

def velocity(x,gamma,core0,ref,exp,require_native=False,component_offsets=None):
    cores=segment_cores(x,ref,core0,exp,component_offsets);return velocity_from_cores(x,gamma,cores,require_native,component_offsets),cores

def uniform_global_volume_cores(x,core0,length_reference,component_offsets=None):
    L=float(np.sum(segment_lengths(x,component_offsets)));L0=max(float(length_reference),1e-15);a=float(core0)*np.sqrt(L0/max(L,1e-15));return np.full(len(x),a,float)

def stretch_rate_py(x,u,component_offsets=None):
    x=np.asarray(x,float);u=np.asarray(u,float);nxt=_next_index(len(x),component_offsets);dx=x[nxt]-x;du=u[nxt]-u;ell=np.maximum(np.linalg.norm(dx,axis=1),1e-15);t=dx/ell[:,None];return np.sum(du*t,axis=1)/ell

def stretch_rate(x,u,component_offsets=None):
    x=np.asarray(x,float);u=np.asarray(u,float);nxt=_next_index(len(x),component_offsets)
    if HAVE_NATIVE and hasattr(_native,'stretch_rate_indexed'):
        return np.asarray(_native.stretch_rate_indexed(np.ascontiguousarray(x,float),np.ascontiguousarray(u,float),np.ascontiguousarray(nxt,np.int64)))
    if HAVE_NATIVE and len(normalize_offsets(component_offsets,len(x)))==2:
        return np.asarray(_native.stretch_rate(np.ascontiguousarray(x,float),np.ascontiguousarray(u,float)))
    return stretch_rate_py(x,u,component_offsets)

def rk4(x,dt,gamma,core0,ref,exp,require_native=False,component_offsets=None):
    f=lambda z:velocity(z,gamma,core0,ref,exp,require_native,component_offsets)[0];k1=f(x);k2=f(x+.5*dt*k1);k3=f(x+.5*dt*k2);k4=f(x+dt*k3);return x+dt*(k1+2*k2+2*k3+k4)/6

def backend_name():
    if HAVE_NATIVE:return 'cpp-pybind11-openmp' if bool(getattr(_native,'openmp',False)) else 'cpp-pybind11'
    return 'python-fallback'
