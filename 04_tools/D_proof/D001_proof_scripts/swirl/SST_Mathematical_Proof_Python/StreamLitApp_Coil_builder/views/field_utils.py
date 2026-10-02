# views/field_utils.py
from __future__ import annotations

import numpy as np
from typing import Tuple

MU0 = 4.0 * np.pi * 1e-7  # H/m
MU0_4PI = MU0 / (4.0 * np.pi)


def field_from_segments(
        points: np.ndarray,
        segments: np.ndarray,
        current: float,
) -> np.ndarray:
    """
    Biot–Savart veld van dunne draadsegmenten.

    Args:
        points: (M,3) veldpunten.
        segments: (N,2,3) [p0, p1] per segment.
        current: stroom in Ampère.

    Returns:
        B: (M,3) veldvector per punt.
    """
    if segments.size == 0:
        return np.zeros_like(points)

    p0 = segments[:, 0, :]  # (N,3)
    p1 = segments[:, 1, :]  # (N,3)
    dl = p1 - p0            # (N,3)
    mid = 0.5 * (p0 + p1)   # (N,3)

    M = points.shape[0]
    B = np.zeros((M, 3), dtype=float)

    for i in range(segments.shape[0]):
        dl_i = dl[i]     # (3,)
        r0_i = mid[i]    # (3,)

        r_vec = points - r0_i  # (M,3)
        r2 = np.sum(r_vec**2, axis=1)
        r = np.sqrt(r2)
        # Singularity-afscherming
        r3 = np.where(r > 1e-9, r2 * r, 1e-27)

        # dl x r
        cross = np.cross(dl_i, r_vec)  # (M,3)
        factor = MU0_4PI * current / r3  # (M,)

        B += cross * factor[:, None]

    return B


def field_from_dipoles(
        points: np.ndarray,
        dipole_positions: np.ndarray,
        dipole_moments: np.ndarray,
) -> np.ndarray:
    """
    Superpositie van magnetische dipoolvelden.

    Args:
        points: (M,3) veldpunten.
        dipole_positions: (N,3)
        dipole_moments:   (N,3) dipoolmoment-oriëntaties (|m|=1) of met amplitude.

    Returns:
        B: (M,3)
    """
    M = points.shape[0]
    B = np.zeros((M, 3), dtype=float)

    if dipole_positions.size == 0:
        return B

    for r0, m in zip(dipole_positions, dipole_moments):
        r_vec = points - r0  # (M,3)
        r2 = np.sum(r_vec**2, axis=1)
        r = np.sqrt(r2)

        # Singularity-afscherming
        mask = r > 1e-9
        r_hat = np.zeros_like(r_vec)
        r_hat[mask] = r_vec[mask] / r[mask, None]

        m_dot_rhat = np.sum(r_hat * m[None, :], axis=1)  # (M,)

        # Dipoolveld: B = μ0/(4πr^3) [3(m·r̂)r̂ - m]
        r3 = np.where(mask, r2 * r, 1e-27)
        pref = MU0_4PI / r3  # (M,)

        term = 3.0 * m_dot_rhat[:, None] * r_hat - m[None, :]
        B += pref[:, None] * term

    return B


def build_segments_from_polylines(polylines: list[np.ndarray]) -> np.ndarray:
    """
    Converteert een lijst polylines (N_i,3) naar segment-array (N_seg,2,3).
    """
    segs = []
    for poly in polylines:
        if poly.shape[0] < 2:
            continue
        s = np.stack([poly[:-1], poly[1:]], axis=1)  # (Ni-1,2,3)
        segs.append(s)
    if not segs:
        return np.zeros((0, 2, 3), dtype=float)
    return np.concatenate(segs, axis=0)


def make_xy_plane_grid(
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        z_plane: float,
        n_x: int,
        n_y: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Maakt een XY-grid op vaste z-hoogte.
    """
    xs = np.linspace(x_min, x_max, n_x)
    ys = np.linspace(y_min, y_max, n_y)
    X, Y = np.meshgrid(xs, ys)
    Z = np.full_like(X, z_plane)
    pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
    return pts, X, Y, Z