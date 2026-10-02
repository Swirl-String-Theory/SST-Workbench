from __future__ import annotations
import math
import numpy as np

PI = math.pi

def biot_savart(points, queries, gamma=1.0, core=0.04):
    p = np.asarray(points, float)
    q = np.asarray(queries, float)
    a = p
    b = np.roll(p, -1, axis=0)
    dl = b - a
    mid = 0.5 * (a + b)
    out = np.zeros_like(q)
    scale = float(gamma) / (4.0 * PI)
    a2 = float(core) ** 2
    for i, x in enumerate(q):
        r = x - mid
        den = (np.einsum('ij,ij->i', r, r) + a2) ** 1.5
        out[i] = scale * np.sum(np.cross(dl, r) / den[:, None], axis=0)
    return out

def centerline_split(points, labels, gamma=1.0, core=0.04, local_span=4):
    p = np.asarray(points, float)
    labels = np.asarray(labels, np.int32).reshape(-1)
    n = len(p)
    if len(labels) != n:
        raise ValueError('labels length must equal points length')
    a = p
    b = np.roll(p, -1, axis=0)
    dl = b - a
    mid = 0.5 * (a + b)
    scale = float(gamma) / (4.0 * PI)
    a2 = float(core) ** 2
    total = np.zeros((n, 3))
    local = np.zeros((n, 3))
    same = np.zeros((n, 3))
    cross = np.zeros((n, 3))
    transition = np.zeros((n, 3))
    seg_label = np.where(labels == np.roll(labels, -1), labels, -1)
    for i, x in enumerate(p):
        r = x - mid
        den = (np.einsum('ij,ij->i', r, r) + a2) ** 1.5
        c = scale * np.cross(dl, r) / den[:, None]
        total[i] = c.sum(axis=0)
        idx = np.arange(n)
        d0 = np.minimum((idx-i) % n, (i-idx) % n)
        idx1 = (idx+1) % n
        d1 = np.minimum((idx1-i) % n, (i-idx1) % n)
        ml = np.minimum(d0, d1) <= int(local_span)
        local[i] = c[ml].sum(axis=0)
        rest = ~ml
        ms = rest & (seg_label == labels[i]) & (seg_label >= 0)
        mc = rest & (seg_label >= 0) & (seg_label != labels[i])
        mt = rest & (seg_label < 0)
        same[i] = c[ms].sum(axis=0)
        cross[i] = c[mc].sum(axis=0)
        transition[i] = c[mt].sum(axis=0)
    return dict(total=total, local=local, same_lobe=same, cross_lobe=cross, transition=transition)

def min_nonlocal_distance(points, skip=8):
    p = np.asarray(points, float)
    n = len(p)
    best = (float('inf'), -1, -1)
    for i in range(n):
        for j in range(i+1, n):
            d = min((j-i) % n, (i-j) % n)
            if d <= skip:
                continue
            dist = float(np.linalg.norm(p[i]-p[j]))
            if dist < best[0]:
                best = (dist, i, j)
    return dict(distance=best[0], i=best[1], j=best[2])

def backend_info():
    return dict(backend='python', sycl_compiled=False, openmp_compiled=False, is_gpu=False, device_name='python')
