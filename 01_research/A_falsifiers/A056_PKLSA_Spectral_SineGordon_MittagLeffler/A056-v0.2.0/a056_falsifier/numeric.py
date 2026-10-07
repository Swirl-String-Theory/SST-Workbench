from __future__ import annotations
import math
import numpy as np
from scipy.special import gammaln, gammasgn
try:
    import _a056_native as _native
except Exception:
    _native=None

def phase_features(phi, dt, ds, boundary='periodic', backend='auto'):
    arr=np.asarray(phi,float); p=np.unwrap(np.unwrap(arr,axis=1),axis=0)
    if _native is not None and backend in ('auto','native'):
        return tuple(np.asarray(x) for x in _native.phase_features(p,float(dt),float(ds),boundary=='periodic'))
    mid=p[1:-1]; y=(p[2:]-2*mid+p[:-2])/(dt*dt)
    if boundary=='periodic':
        ss=(np.roll(mid,-1,axis=1)-2*mid+np.roll(mid,1,axis=1))/(ds*ds); ph=mid
    else:
        ss=(mid[:,2:]-2*mid[:,1:-1]+mid[:,:-2])/(ds*ds); y=y[:,1:-1]; ph=mid[:,1:-1]
    return y,ss,ph

def phase_feature_parity(phi,dt,ds,boundary='periodic'):
    yp,sp,pp=phase_features(phi,dt,ds,boundary,'python')
    if _native is None: return {"available":False,"relative_l2":None,"max_abs":None}
    yn,sn,pn=phase_features(phi,dt,ds,boundary,'native')
    num=np.linalg.norm(yn-yp)+np.linalg.norm(sn-sp)+np.linalg.norm(pn-pp)
    den=np.linalg.norm(yp)+np.linalg.norm(sp)+np.linalg.norm(pp)
    return {"available":True,"relative_l2":float(num/max(den,1e-30)),"max_abs":float(max(np.max(np.abs(yn-yp)),np.max(np.abs(sn-sp)),np.max(np.abs(pn-pp))))}

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

def mittag_leffler_relax(t,tau,alpha):
    t=np.asarray(t,float); x=np.power(np.maximum(t,0)/float(tau),float(alpha))
    if _native is not None:
        try: return np.asarray(_native.mittag_leffler_alpha1_neg(x,float(alpha)))
        except Exception: pass
    return np.array([_ml_series_scalar(float(v),float(alpha)) for v in x],float)

def ml_backend_parity(t,tau,alpha):
    ref=mittag_leffler_python(t,tau,alpha)
    if _native is None: return {"available":False,"relative_l2":None,"max_abs":None}
    x=np.power(np.maximum(np.asarray(t,float),0)/float(tau),float(alpha))
    cand=np.asarray(_native.mittag_leffler_alpha1_neg(x,float(alpha)))
    return {"available":True,"relative_l2":float(np.linalg.norm(cand-ref)/max(np.linalg.norm(ref),1e-30)),
            "max_abs":float(np.max(np.abs(cand-ref)))}

def native_available(): return _native is not None
