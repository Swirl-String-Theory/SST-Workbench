from __future__ import annotations

import math
import numpy as np


def _segments(points: np.ndarray):
    p = np.asarray(points, dtype=float)
    nxt = np.roll(p, -1, axis=0)
    dl = nxt - p
    mid = 0.5 * (p + nxt)
    return dl, mid


def filament_energy(points, rho: float, gamma: float, core_radius: float) -> float:
    p = np.asarray(points, dtype=float)
    dl, mid = _segments(p)
    r = mid[:, None, :] - mid[None, :, :]
    den = np.sqrt(np.sum(r*r, axis=2) + core_radius**2)
    dots = np.einsum("ik,jk->ij", dl, dl)
    return float(rho * gamma**2 * np.sum(dots / den) / (8.0 * math.pi))


def biot_savart_velocity(points, gamma: float, core_radius: float, background) -> np.ndarray:
    p = np.asarray(points, dtype=float)
    bg = np.asarray(background, dtype=float).reshape(3)
    dl, mid = _segments(p)
    r = p[:, None, :] - mid[None, :, :]
    den = (np.sum(r*r, axis=2) + core_radius**2) ** 1.5
    cross = np.cross(dl[None, :, :], r)
    induced = gamma / (4.0 * math.pi) * np.sum(cross / den[:, :, None], axis=1)
    return induced + bg[None, :]
