from __future__ import annotations
import numpy as np
from scipy.optimize import least_squares


def _weights(power):
    w = np.sqrt(np.asarray(power, float))
    w = np.clip(w / np.median(w), 0.2, 5.0)
    return w


def _bic(rss, n, p):
    return float(n*np.log(max(rss/n, 1e-300)) + p*np.log(n))


def fit_weighted_linear(x, y, power, columns):
    w = _weights(power)
    X = np.column_stack(columns)
    Xw = X * w[:,None]
    yw = y*w
    beta, *_ = np.linalg.lstsq(Xw, yw, rcond=None)
    pred = X @ beta
    rss = float(np.sum((w*(y-pred))**2))
    return beta, pred, rss


def fit_models(df, core_radius_m=None):
    x = df.abs_k_rad_m.to_numpy(float)
    y = df.omega_rad_s.to_numpy(float)
    pwr = df.power.to_numpy(float)
    out = {}
    b,pred,rss = fit_weighted_linear(x,y,pwr,[np.ones_like(x),x])
    out["linear"] = {"params":{"intercept_rad_s":float(b[0]),"v_m_s":float(b[1])},"rss":rss,"bic":_bic(rss,len(x),2)}
    b,pred,rss = fit_weighted_linear(x,y,pwr,[np.ones_like(x),x*x])
    out["quadratic"] = {"params":{"intercept_rad_s":float(b[0]),"b_m2_s":float(b[1])},"rss":rss,"bic":_bic(rss,len(x),2)}
    b,pred,rss = fit_weighted_linear(x,y,pwr,[np.ones_like(x),x,x*x])
    out["linear_quadratic"] = {"params":{"intercept_rad_s":float(b[0]),"v0_m_s":float(b[1]),"b_m2_s":float(b[2])},"rss":rss,"bic":_bic(rss,len(x),3)}
    # power law with intercept
    w = _weights(pwr)
    v_guess = max(np.median(y/x), 1e-30)
    def resid(q):
        a, logc, exponent = q
        return w*(y - (a + np.exp(logc)*x**exponent))
    ls = least_squares(resid, x0=[0.0,np.log(v_guess),1.0], bounds=([-np.inf,-100,0.25],[np.inf,100,4.0]), max_nfev=10000)
    a, logc, exponent = ls.x
    rss = float(np.sum(ls.fun**2))
    out["power"]={"params":{"intercept_rad_s":float(a),"coefficient":float(np.exp(logc)),"exponent":float(exponent)},"rss":rss,"bic":_bic(rss,len(x),3)}
    if core_radius_m is not None and np.isfinite(core_radius_m) and core_radius_m>0:
        z = x*x*np.log(1.0/np.maximum(x*core_radius_m,1e-15))
        b,pred,rss=fit_weighted_linear(x,y,pwr,[np.ones_like(x),z])
        out["k2log"]={"params":{"intercept_rad_s":float(b[0]),"coefficient":float(b[1])},"rss":rss,"bic":_bic(rss,len(x),2)}
    return out


def slope_for_cutoff(df, fraction):
    x = df.abs_k_rad_m.to_numpy(float)
    cut = np.quantile(x, fraction)
    sub = df[df.abs_k_rad_m <= cut]
    if len(sub) < 4:
        return None
    x = sub.abs_k_rad_m.to_numpy(float); y=sub.omega_rad_s.to_numpy(float); p=sub.power.to_numpy(float)
    b,_,_ = fit_weighted_linear(x,y,p,[np.ones_like(x),x])
    return float(b[1])
