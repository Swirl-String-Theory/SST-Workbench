"""Clock-free and clocked phase/holonomy observables for the counter-pulley pair.

This module is BLIND: it contains no fine-structure-constant benchmark.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import math
from typing import Any
import numpy as np

from .geometry import _rodrigues


def wrap_angle(angle: float) -> float:
    """Principal angle in (-pi, pi]."""
    x = (float(angle) + math.pi) % (2.0 * math.pi) - math.pi
    if x <= -math.pi:
        x += 2.0 * math.pi
    return x


def principal_turns(angle: float) -> float:
    return wrap_angle(angle) / (2.0 * math.pi)


def project_normal(v: np.ndarray, tangent: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    t = np.asarray(tangent, dtype=float)
    return v - np.einsum("ij,ij->i", v, t)[:, None] * t


def director_holonomy(vector_field: np.ndarray, tangent: np.ndarray) -> dict[str, float]:
    """Normal-bundle holonomy of a nonzero vector field along a closed curve.

    Each director is minimally parallel transported from t_i to t_{i+1}; the signed
    residual angle to the next director is accumulated.  No material frame is used.
    """
    t = np.asarray(tangent, dtype=float)
    q = project_normal(np.asarray(vector_field, dtype=float), t)
    norms = np.linalg.norm(q, axis=1)
    rms = float(np.sqrt(np.mean(norms * norms)))
    if rms <= 0.0 or float(np.min(norms)) <= 1e-14 * rms:
        raise ValueError("director field becomes zero/ill-defined")
    q = q / norms[:, None]
    total = 0.0
    max_step = 0.0
    n = len(q)
    for i in range(n):
        j = (i + 1) % n
        ta, tb = t[i], t[j]
        v = q[i].copy()
        ax = np.cross(ta, tb)
        sn = float(np.linalg.norm(ax))
        cs = float(np.clip(np.dot(ta, tb), -1.0, 1.0))
        if sn > 1e-14:
            v = _rodrigues(v, ax / sn, float(math.atan2(sn, cs)))
        v -= np.dot(v, tb) * tb
        v /= np.linalg.norm(v)
        ang = float(math.atan2(np.dot(tb, np.cross(v, q[j])), np.dot(v, q[j])))
        total += ang
        max_step = max(max_step, abs(ang))
    return {
        "angle_rad": float(total),
        "turns_unwrapped": float(total / (2.0 * math.pi)),
        "turns_principal": float(principal_turns(total)),
        "director_min_norm": float(np.min(norms)),
        "director_rms_norm": rms,
        "min_over_rms": float(np.min(norms) / rms),
        "max_step_angle_rad": float(max_step),
    }


def center_voronoi_ds(centerline: np.ndarray) -> np.ndarray:
    p = np.asarray(centerline, dtype=float)
    seg = np.linalg.norm(np.roll(p, -1, axis=0) - p, axis=1)
    return 0.5 * (seg + np.roll(seg, 1))


def cross_section_omega(r: np.ndarray, u: np.ndarray, tangent: np.ndarray) -> np.ndarray:
    r2 = np.einsum("ij,ij->i", r, r)
    return np.einsum("ij,ij->i", np.cross(r, u), tangent) / r2


def clocked_phases(*, centerline: np.ndarray, tangent: np.ndarray, normal: np.ndarray,
                   u_plus: np.ndarray, u_minus: np.ndarray, offset: float,
                   D: float, gamma_plus: float, gamma_minus: float) -> dict[str, float]:
    """Several pre-registered dynamic-phase diagnostics.

    They are deliberately reported side-by-side; none may be selected using alpha.
    """
    ds = center_voronoi_ds(centerline)
    r_plus = offset * normal
    r_minus = -offset * normal
    op = cross_section_omega(r_plus, u_plus, tangent)
    om = cross_section_omega(r_minus, u_minus, tangent)

    # Actual angular rate of the line joining the two channels.
    d = 2.0 * offset * normal
    du = np.asarray(u_plus) - np.asarray(u_minus)
    omega_sep = np.einsum("ij,ij->i", np.cross(d, du), tangent) / np.einsum("ij,ij->i", d, d)

    gscale = 0.5 * (abs(float(gamma_plus)) + abs(float(gamma_minus)))
    if gscale <= 0.0:
        raise ValueError("nonzero circulation scale required")
    omega_gamma = gscale / (4.0 * math.pi * D * D)

    def integrate_rate(rate: np.ndarray) -> tuple[float, float]:
        phi = float(np.sum((rate / omega_gamma) * (ds / D)))
        return phi / (2.0 * math.pi), principal_turns(phi)

    sep_turns, sep_principal = integrate_rate(omega_sep)
    # Differential rotor phase (half-difference) and counter-gear slip (sum).
    diff_turns, diff_principal = integrate_rate(0.5 * (om - op))
    slip_turns, slip_principal = integrate_rate(op + om)

    # Local-speed clock: dt = ds / U_rms. This avoids a global clock but is an ansatz,
    # because U_rms is not guaranteed to be the longitudinal transport speed.
    urms_local = np.sqrt(0.5 * (np.einsum("ij,ij->i", u_plus, u_plus)
                                + np.einsum("ij,ij->i", u_minus, u_minus)))
    if float(np.min(urms_local)) <= 1e-14:
        speed_phi = float("nan")
        speed_turns = float("nan")
        speed_principal = float("nan")
    else:
        speed_phi = float(np.sum((omega_sep / urms_local) * ds))
        speed_turns = speed_phi / (2.0 * math.pi)
        speed_principal = principal_turns(speed_phi)

    return {
        "omega_plus_mean": float(np.mean(op)),
        "omega_minus_mean": float(np.mean(om)),
        "omega_separation_mean": float(np.mean(omega_sep)),
        "circulation_clock_separation_turns": float(sep_turns),
        "circulation_clock_separation_principal_turns": float(sep_principal),
        "differential_rotor_clock_turns": float(diff_turns),
        "differential_rotor_clock_principal_turns": float(diff_principal),
        "countergear_slip_clock_turns": float(slip_turns),
        "countergear_slip_clock_principal_turns": float(slip_principal),
        "local_speed_clock_separation_turns": float(speed_turns),
        "local_speed_clock_separation_principal_turns": float(speed_principal),
        "local_speed_clock_min_speed": float(np.min(urms_local)),
    }
