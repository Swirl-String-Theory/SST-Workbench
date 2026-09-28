import math
import numpy as np
from scipy.optimize import least_squares
from .models import power_law_fit
from .backend import kelvin_omega as backend_kelvin_omega, torsion_omega as backend_torsion_omega

def _aic(n, rss, npar):
    rss = max(float(rss), np.finfo(float).tiny)
    return n * math.log(rss / n) + 2 * npar

def fit_kelvin(k, omega):
    k = np.asarray(k, float); omega = np.asarray(omega, float)
    x = k * k
    beta = float(np.dot(x, omega) / np.dot(x, x))
    pred = backend_kelvin_omega(k, beta)
    rss = float(np.sum((omega - pred) ** 2))
    return {"beta": beta, "rss": rss, "aic": _aic(len(k), rss, 1), "pred": pred}

def fit_torsion(k, omega):
    k = np.asarray(k, float); omega = np.asarray(omega, float)
    c0 = max(float(np.median(omega / k)), 1e-8)
    g0 = max(float(np.min(omega)) * 0.25, 1e-8)
    def resid(z):
        c, gap = z
        return backend_torsion_omega(k, c, gap) - omega
    sol = least_squares(resid, x0=np.array([c0,g0]), bounds=(np.array([1e-12,0.0]), np.array([np.inf,np.inf])))
    c, gap = map(float, sol.x)
    pred = backend_torsion_omega(k, c, gap)
    rss = float(np.sum((omega-pred)**2))
    return {"c_phase": c, "gap": gap, "rss": rss, "aic": _aic(len(k), rss, 2), "pred": pred}

def classify_dispersion(k, omega, min_delta_aic=6.0, max_relative_rms=0.05):
    k,omega=np.asarray(k,float),np.asarray(omega,float)
    if k.ndim!=1 or omega.shape!=k.shape or len(k)<4 or not np.isfinite(k).all() or not np.isfinite(omega).all() or np.any(k<=0) or np.any(omega<=0) or len(np.unique(k))<4:
        raise ValueError('positive finite independent frequency pairs required')
    if not np.isfinite([min_delta_aic,max_relative_rms]).all() or min_delta_aic<0 or max_relative_rms<=0:
        raise ValueError('invalid classification gate')
    fk = fit_kelvin(k, omega)
    ft = fit_torsion(k, omega)
    pw = power_law_fit(k, omega)
    delta = fk["aic"] - ft["aic"]  # positive -> torsion preferred
    denominator=float(np.linalg.norm(omega))
    fk['relative_rms']=float(np.sqrt(fk['rss'])/denominator)
    ft['relative_rms']=float(np.sqrt(ft['rss'])/denominator)
    reason='relative_information_criterion'
    if delta >= min_delta_aic and ft['relative_rms'] <= max_relative_rms:
        label = "TORSIONAL_LINEAR_GAPPED"
    elif delta <= -min_delta_aic and fk['relative_rms'] <= max_relative_rms:
        label = "KELVIN_QUADRATIC"
    else:
        label = "AMBIGUOUS"
        reason="inadequate_fit_or_insufficient_model_separation"
    return {
        "classification": label,
        "decision_reason": reason,
        "max_relative_rms": float(max_relative_rms),
        "delta_aic_kelvin_minus_torsion": float(delta),
        "power_exponent_p": pw["p"],
        "kelvin": {k:v for k,v in fk.items() if k != "pred"},
        "torsion": {k:v for k,v in ft.items() if k != "pred"},
    }
