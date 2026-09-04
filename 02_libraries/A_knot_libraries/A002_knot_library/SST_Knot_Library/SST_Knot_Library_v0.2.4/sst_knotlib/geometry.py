from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple
import numpy as np

TAU = 2.0 * math.pi


def _closed(points: np.ndarray) -> np.ndarray:
    p = np.asarray(points, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3:
        raise ValueError('points must have shape (N,3)')
    if len(p) < 3:
        raise ValueError('need at least 3 points')
    if np.linalg.norm(p[0] - p[-1]) < 1e-12:
        p = p[:-1]
    return p


def resample_closed(points: np.ndarray, n: int) -> np.ndarray:
    """Uniform arclength resampling of a closed polyline; endpoint is not duplicated."""
    p = _closed(points)
    q = np.vstack([p, p[0]])
    seg = np.linalg.norm(np.diff(q, axis=0), axis=1)
    if np.any(seg <= 0):
        # remove exact duplicates and recurse once
        keep = np.r_[True, seg[:-1] > 1e-15]
        p = p[keep]
        q = np.vstack([p, p[0]])
        seg = np.linalg.norm(np.diff(q, axis=0), axis=1)
    s = np.r_[0.0, np.cumsum(seg)]
    L = s[-1]
    if L <= 0:
        raise ValueError('zero-length curve')
    st = np.linspace(0.0, L, int(n), endpoint=False)
    out = np.empty((len(st), 3), float)
    j = 0
    for i, x in enumerate(st):
        while j + 1 < len(s) and s[j + 1] <= x:
            j += 1
        h = (x - s[j]) / max(s[j + 1] - s[j], 1e-30)
        out[i] = q[j] * (1 - h) + q[j + 1] * h
    return out


def normalize_centerline(points: np.ndarray, target_length: float = 1.0, center: bool = True) -> np.ndarray:
    p = _closed(points).copy()
    if center:
        p -= p.mean(axis=0)
    L = curve_length(p)
    if L <= 0:
        raise ValueError('zero-length curve')
    return p * (float(target_length) / L)


def curve_length(points: np.ndarray) -> float:
    p = _closed(points)
    return float(np.linalg.norm(np.roll(p, -1, axis=0) - p, axis=1).sum())


def classic_trefoil(n: int = 512, scale: float = 0.55, phase: float = 0.0) -> np.ndarray:
    """Independent mathematical implementation of the common trigonometric trefoil embedding."""
    t = np.linspace(0.0, TAU, int(n), endpoint=False) + phase
    x = np.sin(t) + 2.0 * np.sin(2.0 * t)
    y = np.cos(t) - 2.0 * np.cos(2.0 * t)
    z = -np.sin(3.0 * t)
    return float(scale) * np.column_stack([x, y, z])


def torus_knot(p: int, q: int, n: int = 512, R: float = 2.0, a: float = 0.65,
               b: Optional[float] = None, phase_p: float = 0.0, phase_q: float = 0.0,
               basis: Optional[np.ndarray] = None, offset: Optional[Sequence[float]] = None) -> np.ndarray:
    """Anisotropic torus-knot family. b=a gives the standard circular torus cross-section.

    X(t)=U (R+a cos(qt+phase_q)) cos(pt+phase_p)
        +V (R+a cos(qt+phase_q)) sin(pt+phase_p)
        +N b sin(qt+phase_q) + offset
    """
    if p == 0 or q == 0:
        raise ValueError('p and q must be non-zero')
    if b is None:
        b = a
    t = np.linspace(0.0, TAU, int(n), endpoint=False)
    cp = np.cos(p * t + phase_p)
    sp = np.sin(p * t + phase_p)
    cq = np.cos(q * t + phase_q)
    sq = np.sin(q * t + phase_q)
    r = R + a * cq
    xyz = np.column_stack([r * cp, r * sp, b * sq])
    if basis is not None:
        B = np.asarray(basis, dtype=float)
        if B.shape != (3, 3):
            raise ValueError('basis must be (3,3), rows or columns forming an orthonormal basis')
        # interpret columns as U,V,N
        xyz = xyz @ B.T
    if offset is not None:
        xyz = xyz + np.asarray(offset, dtype=float)
    return xyz


def shader_track_trefoil(n: int = 512, baseR: float = 10.0 / math.sqrt(6.0),
                         bulge_R: float = 2.0, z_weave: float = 3.8,
                         plane_offset: float = -5.0 / math.sqrt(3.0)) -> np.ndarray:
    """Trefoil seed family distilled from the uploaded parametric-track construction.

    Uses an orthonormal basis aligned with the uploaded track and independent radial/axial amplitudes.
    No rendering/SDF code is copied.
    """
    N = np.array([1.0, -1.0, -1.0], float); N /= np.linalg.norm(N)
    U = np.array([1.0,  2.0, -1.0], float); U /= np.linalg.norm(U)
    V = np.array([1.0,  0.0,  1.0], float); V /= np.linalg.norm(V)
    basis = np.column_stack([U, V, N])
    return torus_knot(2, 3, n=n, R=baseR, a=bulge_R, b=z_weave,
                      basis=basis, offset=N * plane_offset)


def figure8_s3(n: int = 512, e: float = 0.16, h: float = 0.25,
               plane: Tuple[int, int] = (0, 3), angle: float = 0.35,
               scale: float = 0.25, pole_guard: float = 1e-8) -> np.ndarray:
    """Figure-eight embedding in S^3 followed by an SO(4) plane rotation and stereographic projection.

    This is a fresh mathematical implementation of the S^3 method discussed in the shaders.
    """
    t = np.linspace(0.0, TAU, int(n), endpoint=False)
    aa = e * np.sin(4.0 * t)
    bb = 1.0 - aa * aa
    q = np.column_stack([
        bb * (h * np.cos(t) + (1.0 - h) * np.cos(3.0 * t)),
        bb * (2.0 * math.sqrt(h - h*h) * np.sin(2.0 * t)),
        2.0 * aa,
        bb * (h * np.sin(t) - (1.0 - h) * np.sin(3.0 * t)),
    ]) / (1.0 + aa*aa)[:, None]
    q = rotate_s3(q, plane=plane, angle=angle)
    return stereographic_project(q, pole_guard=pole_guard) * float(scale)


def inverse_stereographic(points: np.ndarray) -> np.ndarray:
    p = _closed(points)
    r2 = np.einsum('ij,ij->i', p, p)
    den = 1.0 + r2
    return np.column_stack([2.0*p[:,0]/den, 2.0*p[:,1]/den, 2.0*p[:,2]/den, (r2-1.0)/den])


def stereographic_project(q: np.ndarray, pole_guard: float = 1e-10) -> np.ndarray:
    q = np.asarray(q, dtype=float)
    if q.ndim != 2 or q.shape[1] != 4:
        raise ValueError('q must have shape (N,4)')
    den = 1.0 - q[:, 3]
    if np.any(np.abs(den) < pole_guard):
        raise ValueError('curve approaches stereographic projection pole')
    return q[:, :3] / den[:, None]


def rotate_s3(q: np.ndarray, plane: Tuple[int, int] = (0, 3), angle: float = 0.0) -> np.ndarray:
    q = np.asarray(q, dtype=float)
    if q.shape[1] != 4:
        raise ValueError('q must have shape (N,4)')
    i, j = plane
    if i == j or not (0 <= i < 4 and 0 <= j < 4):
        raise ValueError('invalid S3 plane')
    c, s = math.cos(angle), math.sin(angle)
    out = q.copy()
    qi, qj = q[:, i].copy(), q[:, j].copy()
    out[:, i] = c * qi + s * qj
    out[:, j] = -s * qi + c * qj
    return out


def s3_deform(points: np.ndarray, angle: float, plane: Tuple[int, int] = (0, 3),
              recenter: bool = True, preserve_length: bool = True) -> np.ndarray:
    p = _closed(points)
    L0 = curve_length(p)
    q = inverse_stereographic(p)
    r = stereographic_project(rotate_s3(q, plane, angle))
    if recenter:
        r -= r.mean(axis=0)
    if preserve_length:
        r *= L0 / curve_length(r)
    return r


def fourier_smooth(points: np.ndarray, modes: int, n_out: Optional[int] = None) -> np.ndarray:
    """Periodic Fourier low-pass representation for imported KnotPlot/Ridgerunner centerlines."""
    p = _closed(points)
    if n_out is None:
        n_out = len(p)
    base = resample_closed(p, len(p))
    F = np.fft.rfft(base, axis=0)
    keep = min(int(modes), len(F)-1)
    F[keep+1:] = 0
    sm = np.fft.irfft(F, n=len(base), axis=0)
    if n_out != len(base):
        sm = resample_closed(sm, n_out)
    return sm


def perturb_normal_modes(points: np.ndarray, amplitude: float, mode: int,
                         phase: float = 0.0) -> np.ndarray:
    from .frames import bishop_frame
    p = resample_closed(points, len(_closed(points)))
    T, E1, E2, _ = bishop_frame(p)
    s = np.arange(len(p), dtype=float) / len(p)
    a = amplitude * np.cos(TAU * mode * s + phase)
    return p + a[:, None] * E1


def lissajous_7_4(n: int = 512, scale: float = 1.0, phases=(0.0,0.0,0.0)) -> np.ndarray:
    """Simple 7_4 Lissajous representative listed by Knot Atlas: x=cos(3t), y=sin(2t), z=sin(7t).

    Useful as an independent topology-controlled seed family; not an ideal geometry claim.
    """
    t=np.linspace(0.0,TAU,int(n),endpoint=False)
    p0,p1,p2=(float(x) for x in phases)
    return float(scale)*np.column_stack([np.cos(3*t+p0),np.sin(2*t+p1),np.sin(7*t+p2)])
