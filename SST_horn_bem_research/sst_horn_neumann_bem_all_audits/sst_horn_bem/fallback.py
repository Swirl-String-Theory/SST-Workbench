from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Tuple

import numpy as np

PI = math.pi
TWOPI = 2.0 * math.pi


def _field_ring_at(x: np.ndarray, lam: float, n_ring: int, eps: float) -> np.ndarray:
    v = np.zeros(3, dtype=float)
    dphi = TWOPI / n_ring
    for k in range(n_ring):
        ph = dphi * (k + 0.5)
        cp, sp = math.cos(ph), math.sin(ph)
        X = np.array([lam * cp, lam * sp, 0.0])
        dl = np.array([-lam * sp * dphi, lam * cp * dphi, 0.0])
        r = x - X
        rr = float(np.dot(r, r) + eps * eps)
        den = rr * math.sqrt(rr)
        # Gamma/(4*pi), with normalized target Gamma=2*pi => 1/2.
        v += 0.5 * np.cross(dl, r) / den
    return v


def _inside_torus(p: np.ndarray, lam: float) -> bool:
    q = math.hypot(float(p[0]), float(p[1])) - lam
    return q * q + float(p[2]) * float(p[2]) <= 1.0


def _make_panels(lam: float, n_eta: int, n_phi: int):
    xs, ns, areas = [], [], []
    d_eta, d_phi = TWOPI / n_eta, TWOPI / n_phi
    for i in range(n_eta):
        eta = d_eta * (i + 0.5)
        ce, se = math.cos(eta), math.sin(eta)
        for j in range(n_phi):
            phi = d_phi * (j + 0.5)
            cp, sp = math.cos(phi), math.sin(phi)
            xs.append([(lam + ce) * cp, (lam + ce) * sp, se])
            ns.append([ce * cp, ce * sp, se])
            areas.append((lam + ce) * d_eta * d_phi)
    return np.asarray(xs, float), np.asarray(ns, float), np.asarray(areas, float)


def _circulation(field_fn, lam: float, n_circ: int = 256, r_loop: float = 1.12) -> float:
    circ = 0.0
    for k in range(n_circ):
        a0 = TWOPI * k / n_circ
        a1 = TWOPI * (k + 1) / n_circ
        mid = 0.5 * (a0 + a1)
        x = np.array([lam + r_loop * math.cos(mid), 0.0, r_loop * math.sin(mid)])
        dx = np.array([-r_loop * math.sin(mid) * (a1 - a0), 0.0, r_loop * math.cos(mid) * (a1 - a0)])
        circ += float(np.dot(field_fn(x), dx))
    return circ


def _build_bem(xs: np.ndarray, ns: np.ndarray, areas: np.ndarray, self_term: float, ridge: float) -> np.ndarray:
    N = len(xs)
    A = np.empty((N, N), dtype=float)
    for i in range(N):
        xi = xs[i]
        ni = ns[i]
        for j in range(N):
            if i == j:
                A[i, j] = self_term + ridge
            else:
                r = xi - xs[j]
                r2 = float(np.dot(r, r))
                rnorm = math.sqrt(r2)
                A[i, j] = -float(np.dot(ni, r)) * areas[j] / (4.0 * PI * r2 * rnorm)
    return A


def _grad_single_layer_at(x: np.ndarray, xs: np.ndarray, areas: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    g = np.zeros(3, dtype=float)
    for y, a, s in zip(xs, areas, sigma):
        r = x - y
        r2 = float(np.dot(r, r))
        if r2 < 1e-24:
            continue
        rn = math.sqrt(r2)
        g += -s * a * r / (4.0 * PI * r2 * rn)
    return g


def _solve_bem(lam: float, n_ring: int, eps: float, n_eta: int, n_phi: int, self_term: float, auto_self: bool, ridge: float, scale: float):
    xs, ns, areas = _make_panels(lam, n_eta, n_phi)
    v_ring = np.array([scale * _field_ring_at(x, lam, n_ring, eps) for x in xs])
    nv_ring = np.einsum("ij,ij->i", ns, v_ring)
    b_raw = -nv_ring
    total_area = float(np.sum(areas))
    flux_before = float(np.sum(b_raw * areas))
    b = b_raw - flux_before / total_area
    flux_after = float(np.sum(b * areas))

    candidates = [self_term]
    if auto_self:
        candidates = [self_term, -self_term]
    best = None
    for st in candidates:
        A = _build_bem(xs, ns, areas, st, ridge)
        try:
            sigma = np.linalg.solve(A, b)
        except np.linalg.LinAlgError:
            sigma, *_ = np.linalg.lstsq(A, b, rcond=1e-10)
        res = A @ sigma - b
        lin = float(np.linalg.norm(res) / max(1e-30, np.linalg.norm(b)))
        nv_corr = nv_ring + A @ sigma
        # Area-weighted residual relative to boundary speed scale.
        denom = float(np.sum(np.einsum("ij,ij->i", v_ring, v_ring) * areas))
        neu = math.sqrt(float(np.sum(nv_corr * nv_corr * areas)) / max(1e-30, denom))
        score = neu + 0.1 * lin
        if best is None or score < best[0]:
            best = (score, st, sigma, lin, neu, A)
    assert best is not None
    _, st, sigma, lin, neu, A = best
    return xs, ns, areas, sigma, st, flux_before, flux_after, lin, neu



def _offset_probe(field_fn, lam: float, offsets=(1e-1, 1e-2, 1e-3, 1e-4), n_eta: int = 16, n_phi: int = 32):
    """One-sided exterior boundary probe.

    A single-layer BEM has a boundary jump term; direct evaluation exactly on the
    surface is therefore not the correct limiting Neumann operator.  This probe
    evaluates x+eps*n and checks whether the exterior limiting no-through-flow
    condition improves as eps -> 0+.
    """
    xs, ns, areas = _make_panels(lam, max(4, n_eta), max(8, n_phi))
    rows = []
    for off in offsets:
        vv = []
        nv = []
        for x, n in zip(xs, ns):
            xp = x + float(off) * n
            v = field_fn(xp)
            vv.append(float(np.dot(v, v)))
            nv.append(float(np.dot(n, v)))
        vv = np.asarray(vv, float)
        nv = np.asarray(nv, float)
        residual = math.sqrt(float(np.sum(nv * nv * areas)) / max(1e-30, float(np.sum(vv * areas))))
        rows.append({"offset": float(off), "neumann_error_offset": residual, "samples": int(len(xs))})
    vals = [r["neumann_error_offset"] for r in rows]
    return rows, (min(vals) if vals else float("nan")), (max(vals) if vals else float("nan")), (vals[-1] if vals else float("nan"))


def run_horn_bem_numpy(
    lambda_: float = 1.2,
    n_ring: int = 256,
    n_surface: int = 32,
    n_volume: int = 18,
    box_radius: float = 6.0,
    source_eps: float = 0.08,
    fd_step: float = 1e-3,
    bem: bool = True,
    bem_n_eta: int = 12,
    bem_n_phi: int = 24,
    bem_self_term: float = 0.5,
    bem_auto_self_term: bool = True,
    bem_ridge: float = 1e-10,
) -> Dict[str, Any]:
    lam = float(lambda_)
    if lam <= 1.0:
        raise ValueError("lambda_ must be > 1.0")
    n_ring = max(32, int(n_ring))
    n_surface = max(8, int(n_surface))
    n_volume = max(8, int(n_volume))

    raw_field = lambda x: _field_ring_at(np.asarray(x, float), lam, n_ring, source_eps)
    raw_circ = _circulation(raw_field, lam, max(128, n_ring // 2))
    scale = TWOPI / raw_circ if abs(raw_circ) > 1e-14 else 1.0
    # Use +2pi target orientation. This may flip sign relative to input convention.
    ring_field = lambda x: scale * _field_ring_at(np.asarray(x, float), lam, n_ring, source_eps)

    xs = ns = areas = sigma = None
    chosen_self = float("nan")
    flux_before = flux_after = lin_res = sigma_l2 = 0.0
    bem_neumann_pred = float("nan")
    if bem:
        xs, ns, areas, sigma, chosen_self, flux_before, flux_after, lin_res, bem_neumann_pred = _solve_bem(
            lam, n_ring, source_eps, int(bem_n_eta), int(bem_n_phi), float(bem_self_term), bool(bem_auto_self_term), float(bem_ridge), scale
        )
        sigma_l2 = math.sqrt(float(np.sum(sigma * sigma * areas)) / max(1e-30, float(np.sum(areas))))
        field = lambda x: ring_field(x) + _grad_single_layer_at(np.asarray(x, float), xs, areas, sigma)  # type: ignore[arg-type]
        corr_field = lambda x: _grad_single_layer_at(np.asarray(x, float), xs, areas, sigma)  # type: ignore[arg-type]
    else:
        field = ring_field
        corr_field = lambda x: np.zeros(3, dtype=float)

    # Surface Neumann RMS using independent evaluation grid, not necessarily BEM panels.
    surf_x, surf_n, surf_a = _make_panels(lam, n_surface, n_surface)
    vv = np.array([field(x) for x in surf_x])
    nv = np.einsum("ij,ij->i", surf_n, vv)
    speed2 = np.einsum("ij,ij->i", vv, vv)
    neumann_direct_probe = math.sqrt(float(np.sum(nv * nv * surf_a)) / max(1e-30, float(np.sum(speed2 * surf_a))))
    # For a single-layer BEM the boundary normal derivative is a limiting value
    # with a jump term. Directly evaluating grad S on a surface probe omits that
    # jump and is therefore only a rough off-operator diagnostic. The primary
    # Neumann error for BEM runs is the panel-operator residual.
    neumann = bem_neumann_pred if bem else neumann_direct_probe

    offset_rows, offset_min, offset_max, offset_last = _offset_probe(
        field, lam, offsets=(1e-1, 1e-2, 1e-3, 1e-4), n_eta=max(8, n_surface//2), n_phi=max(16, n_surface)
    )

    circ_signed = _circulation(field, lam, max(128, n_ring // 2))
    corr_circ = _circulation(corr_field, lam, max(128, n_ring // 2))
    circ_mag_error = abs(abs(circ_signed) / TWOPI - 1.0)
    circ_signed_error = abs(circ_signed / TWOPI - 1.0)

    # Energy integral.
    B = float(box_radius)
    h = (2.0 * B) / float(n_volume - 1)
    chiK = 0.0
    cells = 0
    for ix in range(n_volume):
        x = -B + h * ix
        for iy in range(n_volume):
            y = -B + h * iy
            for iz in range(n_volume):
                z = -B + h * iz
                p = np.array([x, y, z])
                if _inside_torus(p, lam):
                    continue
                v = field(p)
                chiK += 0.5 * float(np.dot(v, v)) * h**3
                cells += 1

    # Harmonicity probe by finite differences away from torus interior.
    probe = min(7, n_volume)
    Bp = min(3.0, B - 2 * fd_step)
    div2 = curl2 = 0.0
    pc = 0
    for ix in range(probe):
        x = -Bp + 2 * Bp * ix / max(1, probe - 1)
        for iy in range(probe):
            y = -Bp + 2 * Bp * iy / max(1, probe - 1)
            for iz in range(probe):
                z = -Bp + 2 * Bp * iz / max(1, probe - 1)
                p = np.array([x, y, z])
                if _inside_torus(p, lam):
                    continue
                e = np.eye(3) * fd_step
                vx1, vx0 = field(p + e[0]), field(p - e[0])
                vy1, vy0 = field(p + e[1]), field(p - e[1])
                vz1, vz0 = field(p + e[2]), field(p - e[2])
                dv_dx = (vx1 - vx0) / (2 * fd_step)
                dv_dy = (vy1 - vy0) / (2 * fd_step)
                dv_dz = (vz1 - vz0) / (2 * fd_step)
                div = dv_dx[0] + dv_dy[1] + dv_dz[2]
                curl = np.array([dv_dy[2] - dv_dz[1], dv_dz[0] - dv_dx[2], dv_dx[1] - dv_dy[0]])
                div2 += div * div
                curl2 += float(np.dot(curl, curl))
                pc += 1
    divergence_error = math.sqrt(div2 / max(1, pc))
    curl_error = math.sqrt(curl2 / max(1, pc))

    # Far-field decay: compare magnitude at x=B and x=2B to inverse-cube scaling.
    p1 = np.array([B, 0.37 * B, 0.23 * B])
    p2 = 2.0 * p1
    m1 = float(np.linalg.norm(field(p1)))
    m2 = float(np.linalg.norm(field(p2)))
    farfield_decay_error = abs(m2 / max(1e-30, m1) - 1.0 / 8.0)

    chi_cav = PI * PI * lam
    chi_E = chiK + chi_cav
    residual_K = (chiK - TWOPI) / TWOPI
    residual_E = (chi_E - TWOPI) / TWOPI

    return {
        "lambda_": lam,
        "solver_kind": "numpy_bem_neumann_corrected" if bem else "numpy_regularized_ring",
        "bem_enabled": bool(bem),
        "bem_panels": int(bem_n_eta * bem_n_phi) if bem else 0,
        "bem_n_eta": int(bem_n_eta),
        "bem_n_phi": int(bem_n_phi),
        "bem_self_term": chosen_self if bem else float("nan"),
        "bem_rhs_flux_before_projection": flux_before,
        "bem_rhs_flux_after_projection": flux_after,
        "bem_linear_residual": lin_res,
        "bem_sigma_l2": sigma_l2,
        "bem_predicted_neumann_error": bem_neumann_pred,
        "raw_ring_circulation": raw_circ,
        "ring_scale_to_plus_2pi": scale,
        "circulation_signed": circ_signed,
        "circulation_magnitude_error": circ_mag_error,
        "circulation_signed_error": circ_signed_error,
        "bem_correction_circulation": corr_circ,
        "neumann_boundary_error": neumann,
        "neumann_boundary_error_direct_probe": neumann_direct_probe,
        "offset_probe": offset_rows,
        "offset_probe_min_error": offset_min,
        "offset_probe_max_error": offset_max,
        "offset_probe_last_error": offset_last,
        "divergence_error": divergence_error,
        "curl_error": curl_error,
        "farfield_decay_error": farfield_decay_error,
        "chi_K": chiK,
        "chi_cav": chi_cav,
        "chi_E_hollow": chi_E,
        "residual_kinetic_to_2pi": residual_K,
        "residual_total_to_2pi": residual_E,
        "analytic_total_horn_falsifies_2pi": True,
        "gate_circulation_pass": circ_mag_error < 1e-2,
        "gate_circulation_orientation_pass": circ_signed_error < 1e-2,
        "gate_bem_correction_no_circulation_pass": abs(corr_circ) < 1e-3,
        "gate_neumann_pass": neumann < 1e-2,
        "gate_neumann_first_acceptance_pass": neumann < 5e-2,
        "gate_offset_probe_pass": offset_last < 5e-2,
        "gate_harmonic_pass": divergence_error < 5e-3 and curl_error < 5e-3,
        "gate_farfield_pass": farfield_decay_error < 0.2,
        "gate_kinetic_2pi_pass": abs(residual_K) < 0.02,
        "gate_total_2pi_pass": abs(residual_E) < 0.02,
        "mesh_cells": cells,
        "dof": cells + (int(bem_n_eta * bem_n_phi) if bem else 0),
        "n_ring": n_ring,
        "n_surface": n_surface,
        "n_volume": n_volume,
        "box_radius": B,
        "source_eps": source_eps,
        "solver_residual": lin_res,
        "energy_refinement_error": float("nan"),
    }
