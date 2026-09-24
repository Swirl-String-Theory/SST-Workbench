"""Cylindrical Chebyshev–Clenshaw–Curtis measure W_r."""

from __future__ import annotations

import numpy as np


def clenshaw_curtis_weights(n_points: int) -> np.ndarray:
    """Weights for ∫_{-1}^{1} f(x) dx at x_j = cos(π j / (n-1))."""
    n_points = int(n_points)
    if n_points < 2:
        raise ValueError("need at least two quadrature nodes")
    n = n_points - 1
    theta = np.pi * np.arange(n_points) / n
    w = np.zeros(n_points)
    for k in range(n_points):
        s = 0.0
        for j in range(1, n // 2 + 1):
            b = 1.0 if (2 * j == n) else 2.0
            s += b * np.cos(2 * j * theta[k]) / (4 * j * j - 1.0)
        w[k] = (2.0 / n) * (1.0 - s)
    w[0] *= 0.5
    w[-1] *= 0.5
    return w


def chebyshev_nodes(n_points: int) -> np.ndarray:
    n = int(n_points)
    j = np.arange(n)
    return np.cos(np.pi * j / (n - 1))


def radial_grid(n_points: int, rmax: float) -> np.ndarray:
    x = chebyshev_nodes(n_points)
    return (1.0 - x) * float(rmax) / 2.0


def cylindrical_weights(r: np.ndarray, rmax: float) -> np.ndarray:
    """Diagonal of W_r for ∫_0^{rmax} g(r) r dr on A029's Chebyshev map."""
    r = np.asarray(r, dtype=float)
    w_x = clenshaw_curtis_weights(r.size)
    return w_x * r * (float(rmax) / 2.0)


def block_measure(w_radial: np.ndarray, n_blocks: int = 4) -> np.ndarray:
    return np.tile(np.asarray(w_radial, dtype=float), int(n_blocks))


def weighted_inner(left, right, weights, mass=None) -> complex:
    p = np.asarray(left, dtype=complex).ravel()
    u = np.asarray(right, dtype=complex).ravel()
    w = np.asarray(weights, dtype=float).ravel()
    if mass is None:
        bu = u
    else:
        bu = np.asarray(mass, dtype=complex) @ u
    if p.size != bu.size or p.size != w.size:
        raise ValueError("left, right, and W_r must share length")
    return complex(np.vdot(p, w * bu))
