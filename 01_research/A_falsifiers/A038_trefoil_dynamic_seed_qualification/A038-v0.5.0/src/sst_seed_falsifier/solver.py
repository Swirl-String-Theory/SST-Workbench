import numpy as np
from .geometry import segment_lengths
try:
    from . import _native
    HAVE_NATIVE=True
except Exception:
    _native=None; HAVE_NATIVE=False

def backend_name():
    if HAVE_NATIVE: return 'cpp-pybind11-openmp' if bool(getattr(_native,'openmp',False)) else 'cpp-pybind11'
    return 'python-fallback'

def velocity_py(x,gamma,cores):
    x=np.asarray(x,float); cores=np.asarray(cores,float); n=len(x); u=np.zeros_like(x); pref=gamma/(4*np.pi)
    for j in range(n):
        k=(j+1)%n; seg=x[k]-x[j]; mid=.5*(x[j]+x[k]); r=x-mid; cr=np.cross(np.broadcast_to(seg,r.shape),r); den=(np.sum(r*r,axis=1)+cores[j]**2)**1.5; u+=pref*cr/den[:,None]
    return u

def velocity_from_cores(x,gamma,cores,require_native=False):
    if HAVE_NATIVE: return np.asarray(_native.velocity_variable_core(np.ascontiguousarray(x,float),float(gamma),np.ascontiguousarray(cores,float)))
    if require_native: raise RuntimeError('Native extension unavailable; run run_01_build_native.cmd')
    return velocity_py(x,gamma,cores)

def stretch_rate_py(x,u):
    dx=np.roll(x,-1,axis=0)-x; du=np.roll(u,-1,axis=0)-u; ell=np.maximum(np.linalg.norm(dx,axis=1),1e-15); t=dx/ell[:,None]; return np.sum(du*t,axis=1)/ell

def stretch_rate(x,u):
    if HAVE_NATIVE: return np.asarray(_native.stretch_rate(np.ascontiguousarray(x,float),np.ascontiguousarray(u,float)))
    return stretch_rate_py(x,u)

def cores_for(x,core0,mode='fixed',ref_lengths=None,L0=None):
    if mode=='fixed': return np.full(len(x),float(core0))
    if mode=='global_volume':
        if L0 is None:
            raise ValueError('L0 required')
        L=float(np.sum(segment_lengths(x)))
        return np.full(len(x),float(core0)*np.sqrt(float(L0)/max(L,1e-15)))
    if mode=='material':
        if ref_lengths is None:
            raise ValueError('ref_lengths required')
        ds=segment_lengths(x)
        return float(core0)*np.sqrt(np.maximum(ref_lengths,1e-15)/np.maximum(ds,1e-15))
    raise ValueError(mode)

def rhs(x,gamma,core0,mode,require_native=False,ref_lengths=None,L0=None):
    c=cores_for(x,core0,mode,ref_lengths,L0); return velocity_from_cores(x,gamma,c,require_native),c

def rk4(x,dt,gamma,core0,mode,require_native=False,ref_lengths=None,L0=None):
    f=lambda z:rhs(z,gamma,core0,mode,require_native,ref_lengths,L0)[0]
    k1=f(x); k2=f(x+.5*dt*k1); k3=f(x+.5*dt*k2); k4=f(x+dt*k3); return x+dt*(k1+2*k2+2*k3+k4)/6
