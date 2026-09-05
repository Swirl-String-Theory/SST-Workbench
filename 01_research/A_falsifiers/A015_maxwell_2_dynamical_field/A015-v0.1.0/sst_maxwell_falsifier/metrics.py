from __future__ import annotations
import numpy as np

EPS = 1e-30


def rms(x) -> float:
    x = np.asarray(x)
    return float(np.sqrt(np.mean(np.abs(x) ** 2)))


def nrmse(pred, obs, floor: float = EPS) -> float:
    return rms(np.asarray(pred) - np.asarray(obs)) / max(rms(obs), floor)


def fit_affine(x, y):
    x = np.asarray(x, dtype=float).reshape(-1)
    y = np.asarray(y, dtype=float).reshape(-1)
    A = np.column_stack([x, np.ones_like(x)])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    a, b = map(float, coef)
    yhat = A @ coef
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / max(ss_tot, EPS)
    return a, b, r2


def fit_powerlaw(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = (x > 0) & (np.abs(y) > max(np.max(np.abs(y)) * 1e-12, EPS))
    if np.count_nonzero(mask) < 4:
        return float("nan"), float("nan")
    lx = np.log(x[mask])
    ly = np.log(np.abs(y[mask]))
    slope, intercept, r2 = fit_affine(lx, ly)
    return float(-slope), float(r2)


def to_jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        if np.iscomplexobj(obj):
            return {"real": obj.real.tolist(), "imag": obj.imag.tolist()}
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, complex):
        return {"real": obj.real, "imag": obj.imag}
    return obj
