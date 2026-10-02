import numpy as np
try:
    from . import _native
    HAVE_NATIVE=True
except Exception:
    _native=None; HAVE_NATIVE=False

def segment_lengths(x):
    return np.linalg.norm(np.roll(np.asarray(x,float),-1,axis=0)-np.asarray(x,float),axis=1)

def segment_cores(x,reference_lengths,core0,core_length_exponent=-0.5):
    ell=np.maximum(segment_lengths(x),1e-15); ref=np.maximum(np.asarray(reference_lengths,float),1e-15)
    return float(core0)*np.power(ell/ref,float(core_length_exponent))

def velocity_python(x,gamma=1.0,core=.05):
    x=np.asarray(x,float); n=len(x); u=np.zeros_like(x); pref=gamma/(4*np.pi); a2=core*core
    for j in range(n):
        k=(j+1)%n; seg=x[k]-x[j]; mid=.5*(x[j]+x[k]); r=x-mid
        cr=np.cross(np.broadcast_to(seg,r.shape),r); den=((r*r).sum(1)+a2)**1.5
        u += pref*cr/den[:,None]
    return u

def velocity_variable_core_python(x,gamma,cores):
    x=np.asarray(x,float); cores=np.asarray(cores,float); n=len(x); u=np.zeros_like(x); pref=gamma/(4*np.pi)
    for j in range(n):
        k=(j+1)%n; seg=x[k]-x[j]; mid=.5*(x[j]+x[k]); r=x-mid
        cr=np.cross(np.broadcast_to(seg,r.shape),r); den=((r*r).sum(1)+cores[j]**2)**1.5
        u += pref*cr/den[:,None]
    return u

def velocity(x,gamma=1.0,core=.05,require_native=False):
    if HAVE_NATIVE: return np.asarray(_native.velocity(np.ascontiguousarray(x,float),float(gamma),float(core)))
    if require_native: raise RuntimeError('Native extension unavailable; run run_build_native.cmd')
    return velocity_python(x,gamma,core)

def velocity_material(x,gamma,core0,reference_lengths,core_length_exponent=-0.5,require_native=False):
    cores=segment_cores(x,reference_lengths,core0,core_length_exponent)
    if HAVE_NATIVE:
        return np.asarray(_native.velocity_variable_core(np.ascontiguousarray(x,float),float(gamma),np.ascontiguousarray(cores,float))),cores
    if require_native: raise RuntimeError('Native extension unavailable; run run_build_native.cmd')
    return velocity_variable_core_python(x,gamma,cores),cores

def stretch_rate_python(x,u):
    dx=np.roll(x,-1,axis=0)-x; du=np.roll(u,-1,axis=0)-u; ell=np.linalg.norm(dx,axis=1); ell=np.maximum(ell,1e-15); t=dx/ell[:,None]
    return (du*t).sum(1)/ell

def stretch_rate(x,u):
    if HAVE_NATIVE: return np.asarray(_native.stretch_rate(np.ascontiguousarray(x,float),np.ascontiguousarray(u,float)))
    return stretch_rate_python(x,u)

def rk4_step_material(x,dt,gamma,core0,reference_lengths,core_length_exponent=-0.5,require_native=False):
    k1,_=velocity_material(x,gamma,core0,reference_lengths,core_length_exponent,require_native)
    k2,_=velocity_material(x+.5*dt*k1,gamma,core0,reference_lengths,core_length_exponent,require_native)
    k3,_=velocity_material(x+.5*dt*k2,gamma,core0,reference_lengths,core_length_exponent,require_native)
    k4,_=velocity_material(x+dt*k3,gamma,core0,reference_lengths,core_length_exponent,require_native)
    return x+(dt/6.0)*(k1+2*k2+2*k3+k4)

def rk4_step(x,dt,gamma,core,require_native=False):
    # compatibility path: fixed core is exponent 0 with reference lengths equal to current lengths
    return rk4_step_material(x,dt,gamma,core,segment_lengths(x),0.0,require_native)

def backend_name():
    if HAVE_NATIVE:
        return 'cpp-pybind11-openmp' if bool(getattr(_native,'openmp',False)) else 'cpp-pybind11'
    return 'python-fallback'
