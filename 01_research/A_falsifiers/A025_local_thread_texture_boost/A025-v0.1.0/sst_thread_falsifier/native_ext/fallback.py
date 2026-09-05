from __future__ import annotations
import numpy as np


def biot_savart(points, component_offsets, gamma=1.0, core_radius=0.05):
    p = np.ascontiguousarray(points, dtype=np.float64)
    offsets = np.asarray(component_offsets, dtype=np.int64)
    n = len(p)
    out = np.zeros((n, 3), dtype=np.float64)
    a2 = float(core_radius) ** 2
    pref = float(gamma) / (4.0 * np.pi)
    for c in range(len(offsets) - 1):
        lo, hi = int(offsets[c]), int(offsets[c + 1])
        if hi - lo < 3:
            continue
        seg_a = p[lo:hi]
        seg_b = np.roll(seg_a, -1, axis=0)
        dl = seg_b - seg_a
        mid = 0.5 * (seg_a + seg_b)
        for i in range(n):
            r = p[i][None, :] - mid
            den = (np.einsum('ij,ij->i', r, r) + a2) ** 1.5
            out[i] += pref * np.sum(np.cross(dl, r) / den[:, None], axis=0)
    return out
