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

def classify_dispersion(k, omega, min_delta_aic=6.0):
    fk = fit_kelvin(k, omega)
    ft = fit_torsion(k, omega)
    pw = power_law_fit(k, omega)
    delta = fk["aic"] - ft["aic"]  # positive -> torsion preferred
    if delta >= min_delta_aic:
        label = "TORSIONAL_LINEAR_GAPPED"
    elif delta <= -min_delta_aic:
        label = "KELVIN_QUADRATIC"
    else:
        label = "AMBIGUOUS"
    return {
        "classification": label,
        "delta_aic_kelvin_minus_torsion": float(delta),
        "power_exponent_p": pw["p"],
        "kelvin": {k:v for k,v in fk.items() if k != "pred"},
        "torsion": {k:v for k,v in ft.items() if k != "pred"},
    }
