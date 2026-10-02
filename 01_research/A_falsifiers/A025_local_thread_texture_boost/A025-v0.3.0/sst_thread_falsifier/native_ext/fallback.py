from __future__ import annotations
import numpy as np


def _segment_velocity_exact(x, p0, p1, core_radius):
    """Exact straight-segment integral for the Rosenhead-regularized Biot--Savart kernel.

    Integrates
        dl x r / (|r|^2 + a^2)^(3/2)
    analytically along each straight polygon edge.  This removes the v0.2 midpoint
    quadrature error while keeping the same finite-core regularization.
    """
    d = p1 - p0
    L = float(np.linalg.norm(d))
    if not np.isfinite(L) or L <= 0.0:
        return np.zeros(3, dtype=float)
    e = d / L
    r0 = x - p0
    z0 = float(np.dot(e, r0))
    rperp = r0 - z0 * e
    A = float(np.dot(rperp, rperp) + float(core_radius) ** 2)
    if A <= 0.0 or not np.isfinite(A):
        return np.zeros(3, dtype=float)
    z1 = z0 - L
    f0 = z0 / (A * np.sqrt(A + z0 * z0))
    f1 = z1 / (A * np.sqrt(A + z1 * z1))
    return np.cross(e, rperp) * (f0 - f1)


def filament_velocity(eval_points, filament_points, component_offsets, gammas, core_radius=0.05):
    x = np.ascontiguousarray(eval_points, dtype=np.float64)
    p = np.ascontiguousarray(filament_points, dtype=np.float64)
    o = np.asarray(component_offsets, dtype=np.int64)
    g = np.asarray(gammas, dtype=np.float64)
    if len(g) != len(o) - 1:
        raise ValueError("gammas must match filament components")
    if float(core_radius) <= 0.0:
        raise ValueError("core_radius must be > 0 for the v0.3 exact regularized segment kernel")
    out = np.zeros((len(x), 3), dtype=np.float64)
    inv4pi = 1.0 / (4.0 * np.pi)
    for ci, (lo, hi) in enumerate(zip(o[:-1], o[1:])):
        lo = int(lo); hi = int(hi)
        if hi - lo < 3:
            continue
        q = p[lo:hi]
        pref = float(g[ci]) * inv4pi
        for i in range(len(x)):
            s = np.zeros(3, dtype=float)
            for j in range(len(q)):
                s += _segment_velocity_exact(x[i], q[j], q[(j + 1) % len(q)], core_radius)
            out[i] += pref * s
    return out


def biot_savart(points, component_offsets, gamma=1.0, core_radius=0.05):
    o = np.asarray(component_offsets, dtype=np.int64)
    g = np.full(len(o) - 1, float(gamma), dtype=np.float64)
    return filament_velocity(points, points, o, g, core_radius)


def _resample_closed_component(q):
    """Redistribute the existing bead count uniformly in polygonal arclength."""
    q = np.asarray(q, dtype=float)
    n = len(q)
    if n < 3:
        return q.copy()
    nxt = np.roll(q, -1, axis=0)
    seg = np.linalg.norm(nxt - q, axis=1)
    L = float(seg.sum())
    if not np.isfinite(L) or L <= 0.0:
        return q.copy()
    s = np.concatenate(([0.0], np.cumsum(seg)))
    targets = np.linspace(0.0, L, n, endpoint=False)
    out = np.empty_like(q)
    j = 0
    for i, t in enumerate(targets):
        while j + 1 < len(s) and s[j + 1] <= t:
            j += 1
        k = j % n
        u = 0.0 if seg[k] <= 0.0 else (t - s[j]) / seg[k]
        out[i] = (1.0 - u) * q[k] + u * q[(k + 1) % n]
    return out


def reparameterize_closed(points, component_offsets):
    P = np.asarray(points, dtype=float)
    O = np.asarray(component_offsets, dtype=np.int64)
    out = P.copy()
    for lo, hi in zip(O[:-1], O[1:]):
        lo = int(lo); hi = int(hi)
        out[lo:hi] = _resample_closed_component(P[lo:hi])
    return out


def _rhs(P, O, gamma, knot_core_radius, T0, TO, TG, thread_core_radius, U, t):
    kg = np.full(len(O) - 1, float(gamma), dtype=float)
    v = filament_velocity(P, P, O, kg, knot_core_radius)
    if len(T0):
        T = T0 + float(t) * U
        v += filament_velocity(P, T, TO, TG, thread_core_radius)
    v += U
    return v


def evolve_frozen_background(points, component_offsets, gamma, knot_core_radius,
                             thread_points, thread_offsets, thread_gammas, thread_core_radius,
                             dt, steps, boost=None, reparameterize_every=0):
    """Classical RK4 evolution in a source-anchored frozen thread substrate.

    The substrate is translated by the same common boost as the knot.  Optional
    arclength redistribution is applied only after complete RK4 steps, so it is a
    numerical parametrization operation rather than an extra restoring force.
    """
    P = np.asarray(points, dtype=float).copy()
    O = np.asarray(component_offsets, dtype=np.int64)
    T0 = np.asarray(thread_points, dtype=float)
    TO = np.asarray(thread_offsets, dtype=np.int64)
    TG = np.asarray(thread_gammas, dtype=float)
    U = np.zeros(3, float) if boost is None else np.asarray(boost, dtype=float)
    dt = float(dt); steps = int(steps); rep = int(reparameterize_every)
    for s in range(steps):
        t = s * dt
        k1 = _rhs(P, O, gamma, knot_core_radius, T0, TO, TG, thread_core_radius, U, t)
        k2 = _rhs(P + 0.5 * dt * k1, O, gamma, knot_core_radius, T0, TO, TG, thread_core_radius, U, t + 0.5 * dt)
        k3 = _rhs(P + 0.5 * dt * k2, O, gamma, knot_core_radius, T0, TO, TG, thread_core_radius, U, t + 0.5 * dt)
        k4 = _rhs(P + dt * k3, O, gamma, knot_core_radius, T0, TO, TG, thread_core_radius, U, t + dt)
        P = P + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        if rep > 0 and (s + 1) % rep == 0:
            P = reparameterize_closed(P, O)
    return P
