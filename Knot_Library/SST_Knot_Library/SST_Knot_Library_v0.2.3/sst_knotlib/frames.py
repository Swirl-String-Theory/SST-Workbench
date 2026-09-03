from __future__ import annotations
import math
import numpy as np
from .geometry import _closed, resample_closed, TAU


def tangents(points: np.ndarray) -> np.ndarray:
    p = _closed(points)
    d = np.roll(p, -1, axis=0) - np.roll(p, 1, axis=0)
    n = np.linalg.norm(d, axis=1)
    return d / np.maximum(n[:,None], 1e-30)


def _rodrigues(v, axis, angle):
    c, s = math.cos(angle), math.sin(angle)
    return v*c + np.cross(axis, v)*s + axis*np.dot(axis, v)*(1.0-c)


def bishop_frame(points: np.ndarray, initial_normal: np.ndarray | None = None, close_holonomy: bool = True):
    """Discrete rotation-minimizing (Bishop/parallel-transport) frame on a closed curve.

    Returns T,E1,E2,holonomy. If close_holonomy=True, distributes residual frame holonomy uniformly.
    """
    p = _closed(points)
    T = tangents(p)
    n = len(p)
    if initial_normal is None:
        axes = np.eye(3)
        a = axes[np.argmin(np.abs(axes @ T[0]))]
        e1 = a - np.dot(a, T[0]) * T[0]
    else:
        a = np.asarray(initial_normal, float)
        e1 = a - np.dot(a, T[0]) * T[0]
    e1 /= np.linalg.norm(e1)
    E1 = np.empty_like(p); E2 = np.empty_like(p)
    E1[0] = e1; E2[0] = np.cross(T[0], E1[0])
    for i in range(1, n):
        a, b = T[i-1], T[i]
        axis = np.cross(a, b)
        sn = np.linalg.norm(axis)
        cs = float(np.clip(np.dot(a,b), -1.0, 1.0))
        if sn < 1e-14:
            v = E1[i-1]
        else:
            axis /= sn
            v = _rodrigues(E1[i-1], axis, math.atan2(sn, cs))
        v -= np.dot(v, b)*b
        v /= np.linalg.norm(v)
        E1[i] = v
        E2[i] = np.cross(b, v)
    # transport last frame once more to T0 and measure residual angle
    a, b = T[-1], T[0]
    axis = np.cross(a,b); sn = np.linalg.norm(axis); cs = float(np.clip(np.dot(a,b),-1,1))
    end = E1[-1]
    if sn >= 1e-14:
        axis /= sn
        end = _rodrigues(end, axis, math.atan2(sn,cs))
    end -= np.dot(end,T[0])*T[0]; end /= np.linalg.norm(end)
    hol = math.atan2(np.dot(end, E2[0]), np.dot(end, E1[0]))
    if close_holonomy:
        # rotate frame around local tangent by -hol*i/n so closure is seamless
        for i in range(n):
            ang = -hol * i / n
            c,s = math.cos(ang), math.sin(ang)
            a1,b1 = E1[i].copy(),E2[i].copy()
            E1[i] = c*a1 + s*b1
            E2[i] = -s*a1 + c*b1
    return T, E1, E2, hol


def thread_bundle(points: np.ndarray, n_threads: int, turns: float, radius: float,
                  phase: float = 0.0, radial_modulation: float = 0.0,
                  modulation_mode: int = 1) -> np.ndarray:
    """Create p material threads around any closed centerline using a Bishop frame.

    Output shape is (n_threads, N, 3). This represents a bundle, not a claim that each thread is a cable-knot component.
    """
    p = _closed(points)
    _, E1, E2, _ = bishop_frame(p)
    s = np.arange(len(p), dtype=float) / len(p)
    out = np.empty((n_threads, len(p), 3), float)
    for j in range(n_threads):
        phi = TAU*turns*s + phase + TAU*j/n_threads
        rr = radius * (1.0 + radial_modulation*np.cos(TAU*modulation_mode*s))
        out[j] = p + rr[:,None]*(np.cos(phi)[:,None]*E1 + np.sin(phi)[:,None]*E2)
    return out


def ribbon_edges(points: np.ndarray, half_width: float, twist_turns: float = 0.0,
                 wave_amplitude: float = 0.0, wave_mode: int = 3, wave_phase: float = 0.0):
    """Two ribbon edges around a centerline. The sinusoidal wave has zero net added twist."""
    p = _closed(points)
    _, E1,E2,_ = bishop_frame(p)
    s = np.arange(len(p), dtype=float)/len(p)
    phi = TAU*twist_turns*s + wave_amplitude*np.sin(TAU*wave_mode*s + wave_phase)
    e = np.cos(phi)[:,None]*E1 + np.sin(phi)[:,None]*E2
    return p + half_width*e, p - half_width*e
