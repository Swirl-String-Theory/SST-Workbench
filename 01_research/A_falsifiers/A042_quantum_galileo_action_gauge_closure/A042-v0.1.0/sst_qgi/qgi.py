from __future__ import annotations
import math
import numpy as np

def gauge_phase(z: float, t: float, m: float, g: float, hbar: float) -> float:
    return (m / hbar) * (-(g*g*t**3)/6.0 - g*z*t)

def ideal_phase(T, m: float, g: float, hbar: float):
    T = np.asarray(T, dtype=float)
    return -(m * g*g * T**3) / (3.0 * hbar)

def generalized_phase(a, T, m: float, g: float, hbar: float):
    T = np.asarray(T, dtype=float)
    a = np.asarray(a, dtype=float)
    return (m * a * (a - 2.0*g) * T**3) / (3.0 * hbar)

def finite_pulse_phase(T, Tkick, Td, m: float, g: float, hbar: float):
    T = np.asarray(T, dtype=float)
    bracket = (
        T**3
        + T**2 * Tkick
        + T * (Tkick**2 + Tkick*Td)
        - Td * (Tkick + Td)**2
    )
    return (m * g*g / (3.0*hbar)) * bracket

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
    # z_E is constant for the ballistic free-fall path after z_E = z_N + g t^2 / 2.
    zE = 0.5*g*T*T
    def F(t):
        return -m*g*t*zE + (m*g*g*t**3)/3.0
    return F(T) - F(-T)

def frame_closure_relative_error(T: float, m: float, g: float, n: int = 2049) -> float:
    s_lab = lab_action_numeric(T, m, g, n)
    s_ff = freefall_boundary_action(T, m, g)
    scale = max(abs(lab_action_analytic(T, m, g)), 1e-300)
    return abs(s_lab - s_ff) / scale

def fit_power_law(T, phase) -> tuple[float, float]:
    T = np.asarray(T, dtype=float)
    y = np.abs(np.asarray(phase, dtype=float))
    mask = (T > 0) & (y > 0)
    x = np.log(T[mask])
    ly = np.log(y[mask])
    p, logA = np.polyfit(x, ly, 1)
    return float(p), float(math.exp(logA))
