from __future__ import annotations
import numpy as np
from .geometry import rz

PXY = np.diag([1.0, 1.0, 0.0])


def envelope(t: float, total_time: float, kind: str = "flat") -> float:
    if kind == "flat":
        return 1.0
    if kind == "sin2":
        x = np.clip(t/total_time, 0.0, 1.0)
        return float(np.sin(np.pi*x)**2)
    raise ValueError(f"unknown envelope {kind}")


def drive_vector(t: float, omega: float, a1: float, a2: float, phase: float,
                 chirality: str) -> np.ndarray:
    """Two-colour planar waveform. CNR has exact threefold dynamical symmetry."""
    if chirality not in {"COR", "CNR"}:
        raise ValueError("chirality must be COR or CNR")
    s2 = +1.0 if chirality == "COR" else -1.0
    e1 = np.array([np.cos(omega*t), np.sin(omega*t), 0.0])
    e2 = np.array([np.cos(2.0*omega*t + phase), s2*np.sin(2.0*omega*t + phase), 0.0])
    return a1*e1 + a2*e2


def vector_to_tracefree_strain(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, float)
    planar_norm2 = float(v[0]*v[0] + v[1]*v[1])
    return np.outer(v, v) - 0.5*planar_norm2*PXY


def drive_matrix(t: float, omega: float, a1: float, a2: float, phase: float,
                 chirality: str, total_time: float, envelope_kind: str = "flat") -> np.ndarray:
    v = drive_vector(t, omega, a1, a2, phase, chirality)
    return envelope(t, total_time, envelope_kind)*vector_to_tracefree_strain(v)


def c3_dynamic_symmetry_residual(omega: float, a1: float, a2: float, phase: float,
                                 chirality: str, samples: int = 96) -> float:
    """Check A(t+T/3)=R A(t) R^T for a flat drive."""
    T = 2.0*np.pi/omega
    R = rz(2.0*np.pi/3.0)
    vals = []
    for t in np.linspace(0.0, T, samples, endpoint=False):
        A0 = drive_matrix(t, omega, a1, a2, phase, chirality, T, "flat")
        A1 = drive_matrix(t+T/3.0, omega, a1, a2, phase, chirality, T, "flat")
        vals.append(np.linalg.norm(A1 - R@A0@R.T)/(np.linalg.norm(A0)+1e-30))
    return float(np.max(vals))
