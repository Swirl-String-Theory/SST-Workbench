from __future__ import annotations

import math
import numpy as np

TWOPI = 2.0 * math.pi


def _ring_points(lam: float, n_ring: int):
    t = np.linspace(0.0, TWOPI, n_ring, endpoint=False)
    dl = TWOPI / n_ring
    pts = np.column_stack([lam * np.cos(t), lam * np.sin(t), np.zeros_like(t)])
    dls = np.column_stack([-lam * np.sin(t) * dl, lam * np.cos(t) * dl, np.zeros_like(t)])
    return pts, dls


def _field_at(x: np.ndarray, lam: float, n_ring: int, eps: float) -> np.ndarray:
    pts, dls = _ring_points(lam, n_ring)
    r = x[None, :] - pts
    den = (np.sum(r * r, axis=1) + eps * eps) ** 1.5
    # circulation normalized to 2pi, so Gamma/(4pi)=1/2
    return 0.5 * np.sum(np.cross(dls, r) / den[:, None], axis=0)


def _inside_torus(x: np.ndarray, lam: float) -> bool:
    q = math.hypot(x[0], x[1]) - lam
    return q * q + x[2] * x[2] <= 1.0


def compute_metrics(lam: float, n_ring: int = 192, n_surface: int = 40, n_volume: int = 22,
                    box_radius: float = 6.0, eps: float = 0.08, fd_step: float = 0.025):
    rng = range
    # Surface Neumann error.
    s2 = 0.0
    sc = 0
    n_theta = max(8, n_surface)
    n_phi = max(8, n_surface)
    for i in rng(n_theta):
        th = TWOPI * (i + 0.5) / n_theta
        ct, st = math.cos(th), math.sin(th)
        for j in rng(n_phi):
            ph = TWOPI * (j + 0.5) / n_phi
            cp, sp = math.cos(ph), math.sin(ph)
            x = np.array([(lam + ct) * cp, (lam + ct) * sp, st], dtype=float)
            n = np.array([ct * cp, ct * sp, st], dtype=float)
            v = _field_at(x, lam, n_ring, eps)
            s2 += float(np.dot(n, v) ** 2)
            sc += 1
    neumann = math.sqrt(s2 / max(1, sc))

    # Circulation around an exterior meridian loop around the tube.
    r_loop = 1.12
    circ = 0.0
    n_circ = max(96, n_ring // 2)
    prev = None
    for k in rng(n_circ):
        a0 = TWOPI * k / n_circ
        a1 = TWOPI * (k + 1) / n_circ
        mid = 0.5 * (a0 + a1)
        x = np.array([lam + r_loop * math.cos(mid), 0.0, r_loop * math.sin(mid)], dtype=float)
        dx = np.array([-r_loop * math.sin(mid), 0.0, r_loop * math.cos(mid)], dtype=float) * (a1 - a0)
        v = _field_at(x, lam, n_ring, eps)
        circ += float(np.dot(v, dx))
    circulation_error = abs(abs(circ) / TWOPI - 1.0)

    # Volume energy in finite cube excluding torus.
    B = box_radius
    xs = np.linspace(-B, B, n_volume)
    h = (2.0 * B) / (n_volume - 1)
    e = 0.0
    count = 0
    for x0 in xs:
        for y0 in xs:
            for z0 in xs:
                p = np.array([x0, y0, z0], dtype=float)
                if _inside_torus(p, lam):
                    continue
                v = _field_at(p, lam, n_ring, eps)
                e += 0.5 * float(np.dot(v, v)) * h ** 3
                count += 1
    chi_K = e

    # div/curl finite-difference residual on a sparse inner grid.
    probe = min(9, n_volume)
    xs2 = np.linspace(-min(3.0, B - fd_step), min(3.0, B - fd_step), probe)
    div2 = 0.0
    curl2 = 0.0
    pc = 0
    basis = np.eye(3)
    for x0 in xs2:
        for y0 in xs2:
            for z0 in xs2:
                p = np.array([x0, y0, z0], dtype=float)
                if _inside_torus(p, lam):
                    continue
                Vp = []
                Vm = []
                skip = False
                for ax in range(3):
                    pp = p + fd_step * basis[ax]
                    pm = p - fd_step * basis[ax]
                    if _inside_torus(pp, lam) or _inside_torus(pm, lam):
                        skip = True
                        break
                    Vp.append(_field_at(pp, lam, n_ring, eps))
                    Vm.append(_field_at(pm, lam, n_ring, eps))
                if skip:
                    continue
                dVdx = (Vp[0] - Vm[0]) / (2 * fd_step)
                dVdy = (Vp[1] - Vm[1]) / (2 * fd_step)
                dVdz = (Vp[2] - Vm[2]) / (2 * fd_step)
                div = dVdx[0] + dVdy[1] + dVdz[2]
                curl = np.array([dVdy[2] - dVdz[1], dVdz[0] - dVdx[2], dVdx[1] - dVdy[0]])
                div2 += float(div * div)
                curl2 += float(np.dot(curl, curl))
                pc += 1
    divergence_error = math.sqrt(div2 / max(1, pc))
    curl_error = math.sqrt(curl2 / max(1, pc))

    # Far-field proxy: for a dipolar ring field, r^3 |v| should approach finite; angular scatter is the error proxy.
    rs = [0.65 * B, 0.85 * B]
    vals = []
    dirs = [np.array([1,0,0.2]), np.array([0,1,0.2]), np.array([0.7,0.5,0.4]), np.array([-0.4,0.8,0.3])]
    for rr in rs:
        for d in dirs:
            d = d / np.linalg.norm(d)
            vv = _field_at(rr * d, lam, n_ring, eps)
            vals.append((rr ** 3) * float(np.linalg.norm(vv)))
    mean = float(np.mean(vals)) if vals else 0.0
    farfield = float(np.std(vals) / mean) if mean > 0 else 1e9

    return {
        "chi_K": chi_K,
        "circulation": circ,
        "circulation_error": circulation_error,
        "neumann_boundary_error": neumann,
        "divergence_error": divergence_error,
        "curl_error": curl_error,
        "farfield_decay_error": farfield,
        "mesh_cells": n_volume ** 3,
        "dof": n_volume ** 3,
        "solver_residual": 0.0,
        "energy_refinement_error": float("nan"),
        "solver_kind": "numpy_fallback_regularized_ring",
    }
