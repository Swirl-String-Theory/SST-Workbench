from __future__ import annotations

from math import sqrt
from typing import Iterable


def quadrupole_rg2(vertices_flat: Iterable[float]) -> dict:
    data = list(float(x) for x in vertices_flat)
    if len(data) % 3 != 0 or not data:
        raise ValueError("vertices_flat must contain 3*N floats")
    n = len(data) // 3
    cx = sum(data[0::3]) / n
    cy = sum(data[1::3]) / n
    cz = sum(data[2::3]) / n
    q = [[0.0, 0.0, 0.0] for _ in range(3)]
    rg2 = 0.0
    for i in range(n):
        x = data[3 * i] - cx
        y = data[3 * i + 1] - cy
        z = data[3 * i + 2] - cz
        r2 = x * x + y * y + z * z
        rg2 += r2
        v = [x, y, z]
        for a in range(3):
            for b in range(3):
                q[a][b] += v[a] * v[b]
        for a in range(3):
            q[a][a] -= r2 / 3.0
    inv = 1.0 / n
    for a in range(3):
        for b in range(3):
            q[a][b] *= inv
    return {"Q": q, "Rg2": rg2 * inv, "centroid": [cx, cy, cz]}


def biot_savart_velocity(
    vertices_flat: Iterable[float],
    samples_flat: Iterable[float],
    gamma: float,
    epsilon_bs: float,
) -> list[float]:
    vertices = list(float(x) for x in vertices_flat)
    samples = list(float(x) for x in samples_flat)
    if len(vertices) % 3 != 0 or len(samples) % 3 != 0:
        raise ValueError("vertices and samples must be flattened 3-vectors")
    if epsilon_bs <= 0:
        raise ValueError("epsilon_bs must be positive")
    n = len(vertices) // 3
    m = len(samples) // 3
    out = [0.0] * (3 * m)
    coeff = gamma / (4.0 * 3.141592653589793)
    eps2 = epsilon_bs * epsilon_bs
    for si in range(m):
        sx, sy, sz = samples[3 * si], samples[3 * si + 1], samples[3 * si + 2]
        ux = uy = uz = 0.0
        for i in range(n):
            j = (i + 1) % n
            x0, y0, z0 = vertices[3 * i], vertices[3 * i + 1], vertices[3 * i + 2]
            x1, y1, z1 = vertices[3 * j], vertices[3 * j + 1], vertices[3 * j + 2]
            dlx, dly, dlz = x1 - x0, y1 - y0, z1 - z0
            mx, my, mz = 0.5 * (x0 + x1), 0.5 * (y0 + y1), 0.5 * (z0 + z1)
            rx, ry, rz = sx - mx, sy - my, sz - mz
            denom = (rx * rx + ry * ry + rz * rz + eps2) ** 1.5
            # dl cross r
            ux += (dly * rz - dlz * ry) / denom
            uy += (dlz * rx - dlx * rz) / denom
            uz += (dlx * ry - dly * rx) / denom
        out[3 * si] = coeff * ux
        out[3 * si + 1] = coeff * uy
        out[3 * si + 2] = coeff * uz
    return out
