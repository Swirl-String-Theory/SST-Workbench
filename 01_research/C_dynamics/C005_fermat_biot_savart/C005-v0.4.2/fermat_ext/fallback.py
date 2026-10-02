from __future__ import annotations

import math
from typing import Callable, Iterable

import numpy as np


def eval_profile(profile: str, x: float, beta0: float, a: float) -> dict[str, float | bool | None]:
    if x < 0 or a <= 0:
        raise ValueError("invalid x or a")
    if profile == "external":
        if x <= 0:
            raise ValueError("x must be positive")
        beta = beta0 / x
        db = -beta0 / x**2
        ddb = 2.0 * beta0 / x**3
    elif profile == "rankine":
        if x < a:
            slope = beta0 / a**2
            beta, db, ddb = slope * x, slope, 0.0
        else:
            beta = beta0 / x
            db = -beta0 / x**2
            ddb = 2.0 * beta0 / x**3
    elif profile == "rosenhead":
        d = x*x + a*a
        beta = beta0 * x / d
        db = beta0 * (a*a - x*x) / d**2
        ddb = beta0 * 2.0*x*(x*x - 3.0*a*a) / d**3
    elif profile == "lamb_oseen":
        if x < 1e-6*a:
            a2, a4, a6 = a*a, a**4, a**6
            beta = beta0 * (x/(2*a2) - x**3/(8*a4) + x**5/(48*a6))
            db = beta0 * (1/(2*a2) - 3*x*x/(8*a4) + 5*x**4/(48*a6))
            ddb = beta0 * (-3*x/(4*a4) + 5*x**3/(12*a6))
        else:
            a2 = a*a
            e = math.exp(-x*x/(2*a2))
            g = 1.0-e
            beta = beta0*g/x
            db = beta0*(e/a2 - g/x**2)
            ddb = beta0*(-e*x/a2**2 - e/(a2*x) + 2*g/x**3)
    else:
        raise ValueError(f"unknown profile: {profile}")

    residual = -x*beta*db - (1.0-beta*beta)
    s2 = 1.0-beta*beta
    if s2 <= 0:
        return {
            "x": x, "beta": beta, "d_beta": db, "dd_beta": ddb,
            "fermat_residual": residual, "clock_valid": False,
            "S": None, "n": None, "R_F_over_rc": None,
            "K_hat": None, "R_F_second_x": None,
        }
    lp = beta*db/s2
    lpp = (((db*db + beta*ddb)*s2) + 2*beta*beta*db*db)/(s2*s2)
    return {
        "x": x, "beta": beta, "d_beta": db, "dd_beta": ddb,
        "fermat_residual": residual, "clock_valid": True,
        "S": math.sqrt(s2), "n": 1.0/math.sqrt(s2),
        "R_F_over_rc": x/math.sqrt(s2),
        "K_hat": -s2*(lpp + lp/x),
        "R_F_second_x": (lp + x*lpp)/math.sqrt(s2),
    }


def _intervals(profile: str, xmin: float, xmax: float, a: float) -> list[tuple[float, float]]:
    if profile == "rankine" and xmin < a < xmax:
        return [(xmin, math.nextafter(a, xmin)), (math.nextafter(a, xmax), xmax)]
    return [(xmin, xmax)]


def _roots(fn: Callable[[float], float], intervals: Iterable[tuple[float, float]], samples: int) -> list[float]:
    roots: list[float] = []
    intervals = list(intervals)
    for lo, hi in intervals:
        n = max(16, samples // max(1, len(intervals)))
        xs = np.geomspace(lo, hi, n+1)
        prev_x, prev_f = float(xs[0]), float(fn(float(xs[0])))
        for x_np in xs[1:]:
            x = float(x_np)
            fx = float(fn(x))
            if math.isfinite(prev_f) and math.isfinite(fx):
                if abs(prev_f) < 1e-13:
                    roots.append(prev_x)
                if prev_f*fx < 0:
                    aa, bb, fa = prev_x, x, prev_f
                    for _ in range(100):
                        mid = 0.5*(aa+bb)
                        fm = float(fn(mid))
                        if abs(fm) < 1e-13 or (bb-aa) < 1e-13*max(1.0, mid):
                            aa = bb = mid
                            break
                        if fa*fm <= 0:
                            bb = mid
                        else:
                            aa, fa = mid, fm
                    roots.append(0.5*(aa+bb))
            prev_x, prev_f = x, fx
    roots.sort()
    out: list[float] = []
    for root in roots:
        if not out or abs(root-out[-1]) > 1e-8*max(1.0, root):
            out.append(root)
    return out


def analyze_profile(profile: str, beta0: float, a: float, xmin: float, xmax: float, samples: int = 4000) -> dict:
    ints = _intervals(profile, xmin, xmax, a)
    def fcrit(x: float) -> float:
        p = eval_profile(profile, x, beta0, a)
        if abs(float(p["beta"])) >= 1.0:
            return math.nan
        return float(p["fermat_residual"])
    def fhor(x: float) -> float:
        return abs(float(eval_profile(profile, x, beta0, a)["beta"])) - 1.0
    critical = _roots(fcrit, ints, samples)
    horizons = _roots(fhor, ints, samples)
    return {
        "profile": profile,
        "beta0": beta0,
        "a_core_over_rc": a,
        "x_min": xmin,
        "x_max": xmax,
        "samples": samples,
        "critical_roots": [eval_profile(profile, x, beta0, a) for x in critical],
        "horizon_roots": [{"x": x, "beta_abs": abs(float(eval_profile(profile, x, beta0, a)["beta"]))} for x in horizons],
    }


def biot_savart_batch(centerline, probes, coefficient: float, epsilon: float, kernel_model: str = "rosenhead_midpoint"):
    c = np.asarray(centerline, dtype=float)
    p = np.asarray(probes, dtype=float)
    if c.ndim != 2 or c.shape[1] != 3 or len(c) < 3:
        raise ValueError("centerline must have shape (N,3), N>=3")
    if p.ndim != 2 or p.shape[1] != 3:
        raise ValueError("probes must have shape (M,3)")
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    if kernel_model != "rosenhead_midpoint":
        raise ValueError(f"unknown kernel_model: {kernel_model}")
    a = c
    b = np.roll(c, -1, axis=0)
    dl = b-a
    mid = 0.5*(a+b)
    out = np.empty_like(p)
    eps2 = epsilon*epsilon
    for j, q in enumerate(p):
        r = q[None, :]-mid
        inv = 1.0/np.power(np.sum(r*r, axis=1)+eps2, 1.5)
        out[j] = coefficient*np.sum(np.cross(dl, r)*inv[:, None], axis=0)
    return out.tolist()


def biot_savart_field_jacobian_batch(
    centerline,
    probes,
    coefficient: float,
    epsilon: float,
    kernel_model: str = "rosenhead_midpoint",
):
    """Evaluate the regularized midpoint Biot--Savart field and its probe Jacobian.

    The Jacobian convention is ``J[i,j] = d beta_i / d x_j``.  This is the
    exact derivative of the discretized Rosenhead midpoint kernel, not a finite
    difference approximation.
    """
    c = np.asarray(centerline, dtype=float)
    p = np.asarray(probes, dtype=float)
    if c.ndim != 2 or c.shape[1] != 3 or len(c) < 3:
        raise ValueError("centerline must have shape (N,3), N>=3")
    if p.ndim != 2 or p.shape[1] != 3:
        raise ValueError("probes must have shape (M,3)")
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    if kernel_model != "rosenhead_midpoint":
        raise ValueError(f"unknown kernel_model: {kernel_model}")

    a = c
    b = np.roll(c, -1, axis=0)
    dl = b - a
    mid = 0.5 * (a + b)
    eps2 = float(epsilon * epsilon)
    beta = np.empty((len(p), 3), dtype=float)
    jac = np.empty((len(p), 3, 3), dtype=float)
    basis = np.eye(3)

    for q_index, q in enumerate(p):
        r = q[None, :] - mid
        q2 = np.sum(r * r, axis=1) + eps2
        inv3 = np.power(q2, -1.5)
        inv5 = np.power(q2, -2.5)
        cross_lr = np.cross(dl, r)
        beta[q_index] = coefficient * np.sum(cross_lr * inv3[:, None], axis=0)
        jmat = np.empty((3, 3), dtype=float)
        for axis in range(3):
            first = np.cross(dl, basis[axis]) * inv3[:, None]
            second = -3.0 * cross_lr * (r[:, axis] * inv5)[:, None]
            jmat[:, axis] = coefficient * np.sum(first + second, axis=0)
        jac[q_index] = jmat
    return {"beta": beta.tolist(), "jacobian": jac.tolist()}
