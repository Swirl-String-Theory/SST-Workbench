from __future__ import annotations
import numpy as np
try:
    import sst_phase_delay_native as _native
    BACKEND="cpp"
except Exception:
    _native=None; BACKEND="python"

def _vel_py(x,gamma,core):
    x=np.asarray(x,float); n=len(x); v=np.zeros_like(x); pref=gamma/(4*np.pi)
    for i in range(n):
        acc=np.zeros(3)
        for j in range(n):
            jp=(j+1)%n
            if j==i or jp==i: continue
            dl=x[jp]-x[j]; mid=.5*(x[jp]+x[j]); r=x[i]-mid; den=(r@r+core*core)**1.5
            acc+=np.cross(dl,r)/den
        v[i]=pref*acc
    return v

def biot_savart_velocity(x,gamma,core):
    return _native.biot_savart_velocity(x,gamma,core) if _native is not None else _vel_py(x,gamma,core)

def _rk4(x,dt,gamma,core):
    k1=_vel_py(x,gamma,core); k2=_vel_py(x+.5*dt*k1,gamma,core); k3=_vel_py(x+.5*dt*k2,gamma,core); k4=_vel_py(x+dt*k3,gamma,core)
    return x+dt*(k1+2*k2+2*k3+k4)/6

def min_gap(x,exclusion=2):
    if _native is not None: return float(_native.min_nonadjacent_segment_distance(x,exclusion))
    # conservative node-node fallback
    n=len(x); best=np.inf
    for i in range(n):
        for j in range(i+1,n):
            d=min(abs(i-j),n-abs(i-j))
            if d<=exclusion: continue
            best=min(best,float(np.linalg.norm(x[i]-x[j])))
    return best

def evolve_pair(a,b,steps,dt,gamma,core,sample_every):
    if _native is not None: return _native.evolve_pair(a,b,steps,dt,gamma,core,sample_every)
    ah=[np.array(a,float)]; bh=[np.array(b,float)]; times=[0.0]; a=ah[0].copy(); b=bh[0].copy()
    for s in range(1,steps+1):
        a=_rk4(a,dt,gamma,core); b=_rk4(b,dt,gamma,core)
        if s%sample_every==0 or s==steps: ah.append(a.copy());bh.append(b.copy());times.append(s*dt)
    return {"times":np.asarray(times),"a":np.asarray(ah),"b":np.asarray(bh),"final_gap_a":min_gap(a),"final_gap_b":min_gap(b)}
