"""Finite-core Rosenhead regularised vortex-filament screening model.

WARNING: NOT a three-dimensional finite-core Euler pressure-Poisson solver.
The regularized filament is a closure; core advection and stretching are NOT
resolved. Energies and generalized forces have SI units.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import numpy as np

TWO_PI = 2.0 * math.pi


def load_seed(path: Path) -> dict:
    obj = json.loads(Path(path).read_text(encoding='utf-8'))
    if obj['id'] != '3:1:1' or obj['D'] != 1.0 or len(obj['coefficients']) < 100:
        raise ValueError('Unexpected ideal-trefoil data')
    return obj


def sample_seed(obj: dict, n: int, dense: int = 4096) -> np.ndarray:
    """Closed periodic Fourier reconstruction with nearly uniform arclength."""
    t = TWO_PI * np.arange(dense) / dense
    curve = np.zeros((dense, 3), dtype=float)
    for co in obj['coefficients']:
        curve += np.outer(np.cos(co['I'] * t), co['A'])
        curve += np.outer(np.sin(co['I'] * t), co['B'])
    if not np.isfinite(curve).all():
        raise ValueError('Nonfinite Fourier reconstruction')
    nxt = np.roll(curve, -1, axis=0)
    arclens = np.linalg.norm(nxt - curve, axis=1)
    cumulative = np.r_[0, np.cumsum(arclens)]
    circumference = cumulative[-1]
    targets = np.arange(n) * circumference / n
    j = np.searchsorted(cumulative, targets, side='right') - 1
    frac = ((targets - cumulative[j]) / np.maximum(arclens[j], 1e-30))[:, None]
    x = curve[j] + frac * (nxt[j] - curve[j])
    x -= np.mean(x, axis=0)
    extent = max(np.linalg.norm(x[:, :2], axis=1))
    return x / extent


def ring(n: int) -> np.ndarray:
    t = TWO_PI * np.arange(n) / n
    return np.stack([np.cos(t), np.sin(t), np.zeros_like(t)], axis=-1)


def length(x: np.ndarray) -> float:
    return float(np.linalg.norm(np.roll(x, -1, axis=0) - x, axis=1).sum())


def segments(x: np.ndarray):
    dx = np.roll(x, -1, axis=0) - x
    mid = 0.5 * (x + np.roll(x, -1, axis=0))
    return mid, dx


def energy(x: np.ndarray, gamma: float, rho: float, core: float) -> float:
    """E = rho Gamma^2/(8 pi) sum_ij (dX_i.dX_j)/sqrt(|mid_i-mid_j|^2+a^2).

    The positive Rosenhead smoothing a regularizes filament self energy.
    """
    if min(gamma, rho, core) <= 0:
        raise ValueError('rho, gamma, core must be positive')
    mid, dx = segments(x)
    disp = mid[:, None, :] - mid[None, :, :]
    dist = np.sqrt(np.einsum('ijk,ijk->ij', disp, disp) + core * core)
    dot = dx @ dx.T
    return float(rho * gamma**2/(8 * math.pi) * np.sum(dot/dist))


def velocity(x: np.ndarray, gamma: float, core: float) -> np.ndarray:
    """Rosenhead-smoothed Biot-Savart filament velocity (m/s)."""
    mid, dx = segments(x)
    r = x[:, None, :] - mid[None, :, :]
    denom = (np.einsum('ijk,ijk->ij', r, r) + core**2)**1.5
    return gamma/(4*math.pi) * np.sum(np.cross(dx[None, :, :], r) / denom[..., None], axis=1)


def relative_equilibrium_residual(x: np.ndarray, u: np.ndarray) -> dict:
    """Projection to normal plane, least-square rigid drift+rotation.
    Tangential filament speed is a geometrical reparametrization gauge.
    """
    tangent = np.roll(x, -1, axis=0) - np.roll(x, 1, axis=0)
    tangent /= np.linalg.norm(tangent, axis=1)[:,None]
    P = np.eye(3)[None,:,:] - tangent[:,:,None]*tangent[:,None,:]
    center = x.mean(axis=0)
    y = x-center
    A = np.zeros((len(x),3,6))
    A[:,:,:3] = np.eye(3)
    for i,(a,b,c) in enumerate(y):
        A[i,:,3:] = [[0,c,-b],[-c,0,a],[b,-a,0]] # Omega cross y
    Ap = np.einsum('nij,njk->nik',P,A).reshape(-1,6)
    up = np.einsum('nij,nj->ni', P,u).reshape(-1)
    w = np.linalg.lstsq(Ap,up,rcond=None)[0]
    err = float(np.linalg.norm(up - Ap@w) / max(np.linalg.norm(up),1e-30))
    return {'normal_residual':err,'translation_m_per_s':w[:3].tolist(),
            'rotation_rad_per_s':w[3:].tolist(), 'velocity_rms_m_per_s':float(np.sqrt(np.mean(np.sum(u*u,axis=1))))}


def min_nonlocal_distance(x: np.ndarray, neighbor_skip: int = 5) -> float:
    mid,_ = segments(x)
    diff = mid[:,None,:]-mid[None,:,:]
    ds = np.linalg.norm(diff,axis=2)
    n=len(x)
    ids=np.arange(n)
    cyc = np.minimum((ids[:,None]-ids[None,:])%n,(ids[None,:]-ids[:,None])%n)
    ds[cyc<=neighbor_skip]=np.inf
    return float(np.min(ds))


def core_at_radius(radius: float, radius0: float, core0: float, protocol: str, gamma0: float) -> tuple[float,float]:
    if protocol=='similarity': return core0*radius/radius0, gamma0
    if protocol=='fixed_core': return core0, gamma0
    if protocol=='fixed_volume': return core0*math.sqrt(radius0/radius), gamma0
    if protocol=='constant_boundary_swirl': return core0*radius/radius0, gamma0*radius/radius0
    raise ValueError(protocol)


def generalised_force(unit: np.ndarray, radius: float, radius0: float, core0: float,
                      protocol: str, gamma0: float, rho: float, h: float = 1e-3) -> tuple[float,float,float]:
    """Force conjugate to global radius: dE/dR (N), NOT a point-to-point load limit."""
    def E(R):
        a,g=core_at_radius(R,radius0,core0,protocol,gamma0)
        return energy(unit*R,g,rho,a)
    force=(E(radius*(1+h))-E(radius*(1-h)))/(2*h*radius)
    a,g = core_at_radius(radius,radius0,core0,protocol,gamma0)
    return float(force),float(E(radius)),float(a)


def rk4(x:np.ndarray, gamma:float, core:float, total_t:float, steps:int) -> np.ndarray:
    """A few diagnostic steps only; without core stretching or pressure closure."""
    dt=total_t/steps
    Y=x.copy()
    for _ in range(steps):
        k1=velocity(Y,gamma,core)
        k2=velocity(Y+0.5*dt*k1,gamma,core)
        k3=velocity(Y+0.5*dt*k2,gamma,core)
        k4=velocity(Y+dt*k3,gamma,core)
        Y += dt*(k1+2*k2+2*k3+k4)/6
    return Y


def probe_deformation_force(unit:np.ndarray, core:float, gamma:float, rho:float,
                            delta:float=0.01) -> float:
    """Local generalized load derivative along a preregistered imposed shape mode.
    NOT a mechanically relaxed clamped shape; does not establish a threshold.
    """
    n=len(unit)
    i=np.arange(n)
    theta=2*math.pi*i/n
    mode=np.exp(-((np.sin((theta-0.8)/2)/0.45)**2))[:,None]*np.array([1.0,0,0])[None,:]
    return float((energy(unit+delta*mode,gamma,rho,core)-energy(unit-delta*mode,gamma,rho,core))/(2*delta))
