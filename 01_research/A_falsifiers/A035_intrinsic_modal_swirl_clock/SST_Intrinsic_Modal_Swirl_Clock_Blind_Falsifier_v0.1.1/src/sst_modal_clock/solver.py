import numpy as np
try:
    from . import _native
    HAVE_NATIVE=True
except Exception:
    _native=None; HAVE_NATIVE=False

def segment_lengths(x): return np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1)
def segment_cores(x,ref,core0,exp): return float(core0)*np.power(np.maximum(segment_lengths(x),1e-15)/np.maximum(ref,1e-15),float(exp))
def velocity_py(x,gamma,cores):
    x=np.asarray(x,float); cores=np.asarray(cores,float); n=len(x); u=np.zeros_like(x); pref=gamma/(4*np.pi)
    for j in range(n):
        k=(j+1)%n; seg=x[k]-x[j]; mid=.5*(x[j]+x[k]); r=x-mid; cr=np.cross(np.broadcast_to(seg,r.shape),r); den=(np.sum(r*r,axis=1)+cores[j]**2)**1.5; u+=pref*cr/den[:,None]
    return u

def velocity(x,gamma,core0,ref,exp,require_native=False):
    cores=segment_cores(x,ref,core0,exp)
    if HAVE_NATIVE: return np.asarray(_native.velocity_variable_core(np.ascontiguousarray(x,float),float(gamma),np.ascontiguousarray(cores,float))),cores
    if require_native: raise RuntimeError('Native extension unavailable; run run_build_native.cmd')
    return velocity_py(x,gamma,cores),cores

def stretch_rate_py(x,u):
    dx=np.roll(x,-1,axis=0)-x; du=np.roll(u,-1,axis=0)-u; ell=np.maximum(np.linalg.norm(dx,axis=1),1e-15); t=dx/ell[:,None]; return np.sum(du*t,axis=1)/ell
def stretch_rate(x,u):
    if HAVE_NATIVE: return np.asarray(_native.stretch_rate(np.ascontiguousarray(x,float),np.ascontiguousarray(u,float)))
    return stretch_rate_py(x,u)
def rk4(x,dt,gamma,core0,ref,exp,require_native=False):
    f=lambda z:velocity(z,gamma,core0,ref,exp,require_native)[0]
    k1=f(x);k2=f(x+.5*dt*k1);k3=f(x+.5*dt*k2);k4=f(x+dt*k3);return x+dt*(k1+2*k2+2*k3+k4)/6
def backend_name():
    if HAVE_NATIVE:return 'cpp-pybind11-openmp' if bool(getattr(_native,'openmp',False)) else 'cpp-pybind11'
    return 'python-fallback'
