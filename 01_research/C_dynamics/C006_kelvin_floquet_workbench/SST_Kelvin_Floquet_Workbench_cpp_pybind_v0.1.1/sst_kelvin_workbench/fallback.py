from __future__ import annotations
import math
import numpy as np


def _as_curve(a, name: str) -> np.ndarray:
    x = np.asarray(a, dtype=float)
    if x.ndim != 2 or x.shape[1] != 3 or x.shape[0] < 3:
        raise ValueError(f"{name} must have shape (N,3), N>=3")
    return np.ascontiguousarray(x)


def interaction_hamiltonian(curve_a, curve_b, gamma_a: float, gamma_b: float, eps: float) -> float:
    a = _as_curve(curve_a, "curve_a")
    b = _as_curve(curve_b, "curve_b")
    if eps <= 0:
        raise ValueError("eps must be > 0")
    da = np.roll(a, -1, axis=0) - a
    db = np.roll(b, -1, axis=0) - b
    ma = 0.5 * (a + np.roll(a, -1, axis=0))
    mb = 0.5 * (b + np.roll(b, -1, axis=0))
    total = 0.0
    for i in range(a.shape[0]):
        r = ma[i] - mb
        den = np.sqrt(np.einsum("ij,ij->i", r, r) + eps * eps)
        total += float(np.sum((db @ da[i]) / den))
    return gamma_a * gamma_b * total / (8.0 * math.pi)


def induced_velocity(targets, filament, gamma: float, eps: float) -> np.ndarray:
    x = _as_curve(targets, "targets")
    q = _as_curve(filament, "filament")
    if eps <= 0:
        raise ValueError("eps must be > 0")
    dl = np.roll(q, -1, axis=0) - q
    mid = 0.5 * (q + np.roll(q, -1, axis=0))
    out = np.zeros_like(x)
    pref = gamma / (4.0 * math.pi)
    for i, xi in enumerate(x):
        r = xi - mid
        r2 = np.einsum("ij,ij->i", r, r) + eps * eps
        den = r2 * np.sqrt(r2)
        out[i] = pref * np.sum(np.cross(dl, r) / den[:, None], axis=0)
    return out


def gauss_linking(curve_a, curve_b) -> float:
    """Midpoint quadrature of the Gauss linking integral."""
    a = _as_curve(curve_a, "curve_a")
    b = _as_curve(curve_b, "curve_b")
    da = np.roll(a, -1, axis=0) - a
    db = np.roll(b, -1, axis=0) - b
    ma = 0.5 * (a + np.roll(a, -1, axis=0))
    mb = 0.5 * (b + np.roll(b, -1, axis=0))
    total = 0.0
    for i in range(a.shape[0]):
        r = ma[i] - mb
        r2 = np.einsum("ij,ij->i", r, r)
        den = r2 * np.sqrt(r2)
        cross = np.cross(np.repeat(da[i][None, :], b.shape[0], axis=0), db)
        total += float(np.sum(np.einsum("ij,ij->i", cross, r) / den))
    return total / (4.0 * math.pi)


def writhe_midpoint(curve) -> float:
    """Principal-value midpoint approximation of polygonal writhe.

    Self and adjacent segment pairs are excluded. The result converges under
    arclength refinement and is used only after an explicit resolution gate.
    """
    c = _as_curve(curve, "curve")
    n = c.shape[0]
    d = np.roll(c, -1, axis=0) - c
    m = 0.5 * (c + np.roll(c, -1, axis=0))
    total = 0.0
    idx = np.arange(n)
    for i in range(n):
        mask = (idx != i) & (idx != (i - 1) % n) & (idx != (i + 1) % n)
        r = m[i] - m[mask]
        r2 = np.einsum("ij,ij->i", r, r)
        den = r2 * np.sqrt(r2)
        cross = np.cross(np.repeat(d[i][None, :], int(np.sum(mask)), axis=0), d[mask])
        total += float(np.sum(np.einsum("ij,ij->i", cross, r) / den))
    return total / (4.0 * math.pi)


def pair_rhs(plus, minus, gamma_plus: float, gamma_minus: float, eps: float) -> np.ndarray:
    """Regularised two-filament Biot--Savart ODE, shape (2N,3)."""
    p = _as_curve(plus, "plus")
    m = _as_curve(minus, "minus")
    if p.shape != m.shape:
        raise ValueError("plus and minus must have the same shape")
    vp = induced_velocity(p, p, gamma_plus, eps) + induced_velocity(p, m, gamma_minus, eps)
    vm = induced_velocity(m, m, gamma_minus, eps) + induced_velocity(m, p, gamma_plus, eps)
    return np.vstack((vp, vm))


def kelvin_long_wave_hat(x: float) -> float:
    if x <= 0:
        raise ValueError("x must be > 0")
    return -0.5*x*x*(math.log(2.0/x) - 0.5772156649015329 + 0.25)


def kelvin_long_wave_hat_array(x) -> np.ndarray:
    a=np.asarray(x,dtype=float)
    if a.ndim != 1:
        raise ValueError("x must be 1D")
    out=np.zeros_like(a)
    mask=a>0
    out[mask]=-0.5*a[mask]**2*(np.log(2.0/a[mask]) - 0.5772156649015329 + 0.25)
    return out


def kelvin_long_wave_si(k: float, a0: float, gamma: float) -> float:
    if a0 <= 0:
        raise ValueError("a0 must be > 0")
    x=abs(k)*a0
    if x == 0:
        return 0.0
    return -(gamma/(4.0*math.pi))*k*k*(math.log(2.0/x)-0.5772156649015329+0.25)


def hollow_core_dispersion_si(k: float, a0: float, gamma: float, m: int=1) -> float:
    if a0 <= 0 or m < 1:
        raise ValueError("a0>0 and m>=1 required")
    x=abs(k)*a0
    if x == 0:
        return 0.0
    try:
        from scipy.special import kv
    except Exception as exc:
        raise RuntimeError("scipy is required by Python fallback hollow-core benchmark") from exc
    Km=float(kv(m,x)); Kprev=float(kv(m-1,x))
    omega0=gamma/(2.0*math.pi*a0*a0)
    return omega0*(1.0-math.sqrt(1.0+x*Kprev/Km))


def backend_info():
    return {"name":"python","kernel":"midpoint_regularized_biot_savart_plus_kelvin_benchmarks"}
