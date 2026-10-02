from __future__ import annotations
import numpy as np
from .geometry import center


def relative_rms(a: np.ndarray,b: np.ndarray,eps: float=1e-30)->float:
    a=np.asarray(a,float); b=np.asarray(b,float)
    num=np.sqrt(np.mean(np.sum((a-b)**2,axis=-1)))
    den=np.sqrt(np.mean(np.sum(center(b)**2,axis=-1)))
    return float(num/max(den,eps))


def relative_scalar(a: float,b: float,eps: float=1e-300)->float:
    return float(abs(a-b)/max(abs(a),abs(b),eps))


def relative_vector(a,b,eps: float=1e-300)->float:
    a=np.asarray(a,float);b=np.asarray(b,float)
    return float(np.linalg.norm(a-b)/max(np.linalg.norm(a),np.linalg.norm(b),eps))


def linear_fit(x,y):
    x=np.asarray(x,float);y=np.asarray(y,float)
    if len(x)<2: return {"slope":float("nan"),"intercept":float("nan"),"r2":float("nan")}
    c=np.polyfit(x,y,1); pred=np.polyval(c,x)
    ssr=float(np.sum((y-pred)**2)); sst=float(np.sum((y-y.mean())**2))
    r2=1.0-ssr/sst if sst>0 else (1.0 if ssr==0 else float("nan"))
    return {"slope":float(c[0]),"intercept":float(c[1]),"r2":float(r2)}


def phase_frequency(time_s: np.ndarray, coeff: np.ndarray, min_power: float=1e-24) -> dict:
    t=np.asarray(time_s,float); q=np.asarray(coeff,complex)
    power=np.abs(q)**2
    if len(t)<4 or not np.isfinite(power).all() or float(np.median(power))<=min_power:
        return {"ok":False,"reason":"insufficient mode power"}
    phase=np.unwrap(np.angle(q))
    fit=linear_fit(t,phase)
    span=float(abs(phase[-1]-phase[0]))
    nu=abs(fit["slope"])/(2*np.pi)
    return {"ok":bool(np.isfinite(nu) and nu>0),"nu_Hz":float(nu),"omega_rad_s":float(abs(fit["slope"])),
            "phase_span_rad":span,"phase_fit_r2":float(fit["r2"]),"phase":phase}


def loglog_slope(x,y):
    x=np.asarray(x,float);y=np.asarray(y,float)
    m=(x>0)&(y>0)&np.isfinite(x)&np.isfinite(y)
    if m.sum()<2: return {"slope":float("nan"),"r2":float("nan")}
    return linear_fit(np.log(x[m]),np.log(y[m]))
