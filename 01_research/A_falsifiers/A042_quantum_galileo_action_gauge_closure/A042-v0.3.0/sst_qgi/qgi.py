from __future__ import annotations
import math
import numpy as np

def ideal_action(T, m: float, g: float):
    T = np.asarray(T, dtype=float)
    return -(m * g*g * T**3) / 3.0

def generalized_action(a, T, m: float, g: float):
    T = np.asarray(T, dtype=float)
    a = np.asarray(a, dtype=float)
    return (m * a * (a - 2.0*g) * T**3) / 3.0

def finite_pulse_action(T, Tkick, Td, m: float, g: float):
    T = np.asarray(T, dtype=float)
    bracket = (
        T**3
        + T**2 * Tkick
        + T * (Tkick**2 + Tkick*Td)
        - Td * (Tkick + Td)**2
    )
    return (m * g*g / 3.0) * bracket

def phase_from_action(action, reduced_action_quantum: float):
    return np.asarray(action, dtype=float) / float(reduced_action_quantum)

def lab_action_analytic(T: float, m: float, g: float) -> float:
    return -(m * g*g * T**3) / 3.0

def _native():
    try:
        import sst_qgi_native
        return sst_qgi_native
    except Exception:
        return None

def lab_action_numeric(T: float, m: float, g: float, n: int = 2049) -> float:
    native = _native()
    if native is not None:
        return float(native.lab_action_uniform_g(T, m, g, int(n)))
    if n % 2 == 0:
        n += 1
    t = np.linspace(-T, T, n)
    z = 0.5*g*(T*T - t*t)
    v = -g*t
    L = 0.5*m*v*v - m*g*z
    return float(np.trapezoid(L, t))

def freefall_boundary_action(T: float, m: float, g: float) -> float:
    zE = 0.5*g*T*T
    def F(t):
        return -m*g*t*zE + (m*g*g*t**3)/3.0
    return F(T) - F(-T)

def fit_power_law(T, y) -> tuple[float, float]:
    T = np.asarray(T, dtype=float)
    y = np.abs(np.asarray(y, dtype=float))
    mask = (T > 0) & (y > 0)
    x = np.log(T[mask])
    ly = np.log(y[mask])
    p, logA = np.polyfit(x, ly, 1)
    return float(p), float(math.exp(logA))
