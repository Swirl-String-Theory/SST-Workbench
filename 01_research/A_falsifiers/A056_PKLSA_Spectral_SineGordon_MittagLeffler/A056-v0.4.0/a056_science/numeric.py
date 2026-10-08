from __future__ import annotations
from pathlib import Path
from functools import lru_cache
import math
import numpy as np
from scipy.special import gammaln, gammasgn

ROOT=Path(__file__).resolve().parents[1]

@lru_cache(maxsize=1)
def _native_cached():
    from sst_falsifier.backends.cpp_pybind import load
    try:
        mod, build = load(ROOT, force_build=False, require=False, verbose=False)
        return mod, build
    except Exception:
        return None, None


def native_info():
    mod,build=_native_cached()
    info={}
    if mod is not None and hasattr(mod,'backend_info'):
        try: info=dict(mod.backend_info())
        except Exception: info={}
    return {"available":mod is not None,"backend_info":info,"build":build.to_dict() if build is not None else None}


def native_available(): return bool(native_info()['available'])


def phase_features(phi, dt, ds, boundary='periodic', backend='python'):
    arr=np.asarray(phi,float); p=np.unwrap(np.unwrap(arr,axis=1),axis=0)
    if backend=='native':
        mod,_=_native_cached()
        if mod is None: raise RuntimeError('C++ certification backend unavailable')
        return tuple(np.asarray(x) for x in mod.phase_features(p,float(dt),float(ds),boundary=='periodic'))
    mid=p[1:-1]; y=(p[2:]-2*mid+p[:-2])/(dt*dt)
    if boundary=='periodic':
        ss=(np.roll(mid,-1,axis=1)-2*mid+np.roll(mid,1,axis=1))/(ds*ds); ph=mid
    else:
        ss=(mid[:,2:]-2*mid[:,1:-1]+mid[:,:-2])/(ds*ds); y=y[:,1:-1]; ph=mid[:,1:-1]
    return y,ss,ph


def phase_feature_parity(phi,dt,ds,boundary='periodic'):
    yp,sp,pp=phase_features(phi,dt,ds,boundary,'python')
    mod,_=_native_cached()
    if mod is None: return {"available":False,"relative_l2":None,"max_abs":None}
    yn,sn,pn=phase_features(phi,dt,ds,boundary,'native')
    num=np.linalg.norm(yn-yp)+np.linalg.norm(sn-sp)+np.linalg.norm(pn-pp)
    den=np.linalg.norm(yp)+np.linalg.norm(sp)+np.linalg.norm(pp)
    return {"available":True,"relative_l2":float(num/max(den,1e-30)),
            "max_abs":float(max(np.max(np.abs(yn-yp)),np.max(np.abs(sn-sp)),np.max(np.abs(pn-pp))))}


def _ml_series_scalar(x,alpha,tol=1e-13,max_terms=500):
    if x==0: return 1.0
    if abs(alpha-1.0)<1e-12: return math.exp(-x)
    total=np.longdouble(1.0)
    for k in range(1,max_terms+1):
        logmag=k*math.log(x)-float(gammaln(alpha*k+1.0))
        mag=np.longdouble(math.exp(logmag)) if logmag<700 else np.longdouble('inf')
        term=-mag if k%2 else mag; total2=total+term
        if np.isfinite(total2) and abs(term)<=tol*max(1.0,abs(total2)) and k>8: return float(total2)
        total=total2
        if not np.isfinite(total): break
    if 0<alpha<1 and x>2.5:
        s=0.0
        for k in range(1,12):
            arg=1.0-alpha*k; lg=float(gammaln(arg)); sg=float(gammasgn(arg))
            if sg==0 or not math.isfinite(lg): continue
            term=(((-1)**(k+1))*sg*math.exp(-lg))/(x**k); s+=term
            if abs(term)<tol*max(1.0,abs(s)): break
        return float(s)
    return float(total)


def mittag_leffler_python(t,tau,alpha):
    t=np.asarray(t,float); x=np.power(np.maximum(t,0)/float(tau),float(alpha))
    return np.array([_ml_series_scalar(float(v),float(alpha)) for v in x],float)


def mittag_leffler_relax(t,tau,alpha,backend='python'):
    t=np.asarray(t,float); x=np.power(np.maximum(t,0)/float(tau),float(alpha))
    if backend=='native':
        mod,_=_native_cached()
        if mod is None: raise RuntimeError('C++ certification backend unavailable')
        return np.asarray(mod.mittag_leffler_alpha1_neg(x,float(alpha)))
    return np.array([_ml_series_scalar(float(v),float(alpha)) for v in x],float)


def ml_backend_parity(t,tau,alpha):
    ref=mittag_leffler_python(t,tau,alpha)
    mod,_=_native_cached()
    if mod is None: return {"available":False,"relative_l2":None,"max_abs":None}
    cand=mittag_leffler_relax(t,tau,alpha,'native')
    return {"available":True,"relative_l2":float(np.linalg.norm(cand-ref)/max(np.linalg.norm(ref),1e-30)),
            "max_abs":float(np.max(np.abs(cand-ref)))}
