"""Pure-Python kernels. Usable for tiny smoke/parity; not for heavy M x N."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

PI = math.pi


def circle(n: int = 512, radius: float = 4.0) -> np.ndarray:
    t = np.linspace(0.0, 2.0 * np.pi, int(n), endpoint=False)
    return np.column_stack([radius * np.cos(t), radius * np.sin(t), np.zeros_like(t)])


def default_queries(m: int, radius: float = 10.0) -> np.ndarray:
    m = int(m)
    t = np.linspace(0.0, 2.0 * np.pi, m, endpoint=False)
    z = np.linspace(-1.0, 1.0, m, endpoint=False)
    r = np.sqrt(np.maximum(1.0 - z * z, 0.0))
    return np.column_stack([radius * r * np.cos(t), radius * r * np.sin(t), radius * z])


def vec_add(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    aa = np.asarray(a, dtype=float).reshape(-1)
    bb = np.asarray(b, dtype=float).reshape(-1)
    if aa.shape != bb.shape:
        raise ValueError("vec_add: a and b must have the same length")
    return aa + bb


def min_abs(x: np.ndarray) -> float:
    xx = np.asarray(x, dtype=float).reshape(-1)
    if xx.size == 0:
        return float("inf")
    return float(np.min(np.abs(xx)))


def biot_savart(
    points: np.ndarray,
    queries: np.ndarray,
    gamma: float = 1.0,
    core: float = 1.0,
) -> np.ndarray:
    """Regularized midpoint Biot-Savart (velocity only). Matches cpp/native.cpp."""
    p = np.asarray(points, dtype=float)
    q = np.asarray(queries, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3:
        raise ValueError("points must be Nx3")
    if q.ndim != 2 or q.shape[1] != 3:
        raise ValueError("queries must be Mx3")
    n = len(p)
    if n < 2:
        raise ValueError("need >=2 filament points")
    nxt = np.roll(p, -1, axis=0)
    dl = nxt - p
    mid = 0.5 * (p + nxt)
    scale = float(gamma) / (4.0 * PI)
    a2 = float(core) ** 2
    vel = np.zeros((len(q), 3), dtype=float)
    for s in range(n):
        r = q - mid[s]
        d = np.sum(r * r, axis=1) + a2
        inv3 = d**-1.5
        cr = np.cross(np.broadcast_to(dl[s], r.shape), r)
        vel += scale * cr * inv3[:, None]
    return vel


def python_backend_info(*, last_kernel_ms: float = 0.0) -> dict[str, Any]:
    return {
        "backend": "python",
        "sycl_compiled": False,
        "openmp_compiled": False,
        "is_gpu": False,
        "device_name": "host-python",
        "queue_reused": False,
        "last_kernel_ms": float(last_kernel_ms),
        "openmp_max_threads": 1,
    }
