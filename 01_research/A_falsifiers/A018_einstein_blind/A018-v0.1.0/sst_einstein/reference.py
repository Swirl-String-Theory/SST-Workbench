from __future__ import annotations
import math
import numpy as np

FOUR_PI = 4.0 * math.pi
EIGHT_PI = 8.0 * math.pi


def _segments(points: np.ndarray):
    p = np.asarray(points, dtype=float)
    q = np.roll(p, -1, axis=0)
    dl = q - p
    mid = 0.5*(p+q)
    return p, dl, mid


def biot_savart_velocity(points: np.ndarray, core: float, gamma: float = 1.0,
                         uniform_velocity=(0.0, 0.0, 0.0)) -> np.ndarray:
    p = np.asarray(points, dtype=float)
    _, dl, mid = _segments(p)
    r = p[:, None, :] - mid[None, :, :]
    r2 = np.sum(r*r, axis=2) + core*core
    cross = np.cross(dl[None, :, :], r)
    vel = gamma/FOUR_PI * np.sum(cross / (r2[..., None]**1.5), axis=1)
    vel += np.asarray(uniform_velocity, dtype=float)
    return vel


def filament_energy(points: np.ndarray, core: float, rho: float = 1.0,
                    gamma: float = 1.0) -> float:
    _, dl, mid = _segments(points)
    r = mid[:, None, :] - mid[None, :, :]
    den = np.sqrt(np.sum(r*r, axis=2) + core*core)
    dot = np.einsum("ik,jk->ij", dl, dl)
    return float(rho*gamma*gamma/EIGHT_PI * np.sum(dot/den))


def impulse(points: np.ndarray, rho: float = 1.0, gamma: float = 1.0) -> np.ndarray:
    p = np.asarray(points, dtype=float)
    q = np.roll(p, -1, axis=0)
    # Integral X x dX; exact polygon form via p x q.
    return 0.5*rho*gamma*np.sum(np.cross(p, q), axis=0)


def curvature(points: np.ndarray) -> np.ndarray:
    p = np.asarray(points, dtype=float)
    pm = np.roll(p, 1, axis=0); pp = np.roll(p, -1, axis=0)
    a = p-pm; b = pp-p
    la = np.linalg.norm(a, axis=1); lb = np.linalg.norm(b, axis=1)
    c = pp-pm; lc = np.linalg.norm(c, axis=1)
    num = 2.0*np.linalg.norm(np.cross(a,b), axis=1)
    den = np.maximum(la*lb*lc, 1e-300)
    return num/den


def rk4_step(points: np.ndarray, dt: float, core: float, gamma: float = 1.0,
             uniform_velocity=(0.0,0.0,0.0)) -> np.ndarray:
    p = np.asarray(points, dtype=float)
    u = np.asarray(uniform_velocity, dtype=float)
    k1 = biot_savart_velocity(p, core, gamma, u)
    k2 = biot_savart_velocity(p + 0.5*dt*k1, core, gamma, u)
    k3 = biot_savart_velocity(p + 0.5*dt*k2, core, gamma, u)
    k4 = biot_savart_velocity(p + dt*k3, core, gamma, u)
    return p + dt*(k1 + 2*k2 + 2*k3 + k4)/6.0
