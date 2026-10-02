import numpy as np
try:
    from . import _native; HAVE_NATIVE=True
except Exception:
    _native=None; HAVE_NATIVE=False

def segment_lengths(x): return np.linalg.norm(np.roll(np.asarray(x,float),-1,axis=0)-np.asarray(x,float),axis=1)
def segment_cores(x,reference_lengths,core0,exponent=-0.5):
    ell=np.maximum(segment_lengths(x),1e-15); ref=np.maximum(np.asarray(reference_lengths,float),1e-15); return float(core0)*np.power(ell/ref,float(exponent))
def velocity_variable_core_python(x,gamma,cores):
    x=np.asarray(x,float); cores=np.asarray(cores,float); n=len(x); u=np.zeros_like(x); pref=gamma/(4*np.pi)
    for j in range(n):
        k=(j+1)%n; seg=x[k]-x[j]; mid=.5*(x[j]+x[k]); r=x-mid; cr=np.cross(np.broadcast_to(seg,r.shape),r); den=((r*r).sum(1)+cores[j]**2)**1.5; u += pref*cr/den[:,None]
    return u
def velocity_material(x,gamma,core0,reference_lengths,exponent=-0.5,require_native=False):
    cores=segment_cores(x,reference_lengths,core0,exponent)
    if HAVE_NATIVE: return np.asarray(_native.velocity_variable_core(np.ascontiguousarray(x,float),float(gamma),np.ascontiguousarray(cores,float))),cores
    if require_native: raise RuntimeError('Native extension unavailable; run run_build_native.cmd')
    return velocity_variable_core_python(x,gamma,cores),cores
def rk4(x,dt,gamma,core0,ref,exponent=-0.5,require_native=False):
    def vel(z): return velocity_material(z,gamma,core0,ref,exponent,require_native)[0]
    k1=vel(x); k2=vel(x+.5*dt*k1); k3=vel(x+.5*dt*k2); k4=vel(x+dt*k3); return x+dt*(k1+2*k2+2*k3+k4)/6
def backend_name():
    if HAVE_NATIVE: return 'cpp-pybind11-openmp' if bool(getattr(_native,'openmp',False)) else 'cpp-pybind11'
    return 'python-fallback'
