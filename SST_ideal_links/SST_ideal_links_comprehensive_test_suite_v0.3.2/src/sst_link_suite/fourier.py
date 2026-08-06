from __future__ import annotations
import numpy as np
from .models import FourierComponent, SampledComponent

# Gilbert uses the conventional Fourier constant term A_0/2.
def evaluate(component: FourierComponent, t: np.ndarray, derivative: int = 0) -> np.ndarray:
    t = np.asarray(t, dtype=float).reshape(-1)
    out = np.zeros((t.size, 3), dtype=float)
    if derivative == 0:
        out += component.A[0][None, :] / 2.0
    if component.A.shape[0] <= 1:
        return out
    n = np.arange(1, component.A.shape[0], dtype=float)
    ang = t[:, None] * n[None, :]
    c, s = np.cos(ang), np.sin(ang)
    A, B = component.A[1:], component.B[1:]
    if derivative == 0:
        out += c @ A + s @ B
    elif derivative == 1:
        out += (-s * n) @ A + (c * n) @ B
    elif derivative == 2:
        out += (-c * n**2) @ A + (-s * n**2) @ B
    elif derivative == 3:
        out += (s * n**3) @ A + (-c * n**3) @ B
    else:
        # General phase-shift form d^k cos(nt)/dt^k = n^k cos(nt+k*pi/2).
        phase = derivative * np.pi / 2.0
        out += (np.cos(ang + phase) * n**derivative) @ A
        out += (np.sin(ang + phase) * n**derivative) @ B
    return out

def sample_component(component: FourierComponent, n: int) -> SampledComponent:
    if n < 16:
        raise ValueError("At least 16 periodic samples are required")
    t = np.arange(n, dtype=float) * (2.0 * np.pi / n)
    return SampledComponent(
        t=t,
        r=evaluate(component, t, 0),
        d1=evaluate(component, t, 1),
        d2=evaluate(component, t, 2),
        d3=evaluate(component, t, 3),
        component=component,
    )

def coefficient_power(component: FourierComponent) -> np.ndarray:
    return np.sum(component.A**2 + component.B**2, axis=1)
