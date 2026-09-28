import numpy as np

def kelvin_omega(k, beta):
    k = np.asarray(k, dtype=float)
    return beta * k * k

def torsion_omega(k, c_phase, gap):
    k = np.asarray(k, dtype=float)
    return np.sqrt((c_phase * k) ** 2 + gap ** 2)

def power_law_fit(k, omega):
    k = np.asarray(k, dtype=float)
    omega = np.asarray(omega, dtype=float)
    if np.any(k <= 0) or np.any(omega <= 0):
        raise ValueError("power_law_fit requires positive k and omega")
    x = np.log(k)
    y = np.log(omega)
    A = np.column_stack([np.ones_like(x), x])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    log_amp, p = coef
    pred = np.exp(log_amp + p * x)
    return {"amplitude": float(np.exp(log_amp)), "p": float(p), "pred": pred}
