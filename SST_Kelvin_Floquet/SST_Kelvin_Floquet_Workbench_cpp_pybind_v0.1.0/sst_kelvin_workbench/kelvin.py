from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
from scipy.optimize import brentq
from scipy.special import jv, jvp, kv, kvp

from .backend import load_backend
from .orbit import kabsch_row, rk4_step

EULER_GAMMA = 0.5772156649015328606


def long_wave_omega(k: float | np.ndarray, a0: float, gamma: float) -> np.ndarray:
    k = np.asarray(k, dtype=float)
    x = np.abs(k) * float(a0)
    out = np.zeros_like(k)
    mask = x > 0
    out[mask] = -(float(gamma) / (4.0 * math.pi)) * k[mask] ** 2 * (
        np.log(2.0 / x[mask]) - EULER_GAMMA + 0.25
    )
    return out


def rankine_residual(omega: float, k: float, *, a0: float, gamma: float,
                      vz: float, m: int = 1) -> complex:
    """Residual of the Rankine-vortex Kelvin dispersion relation used in the paper.

    The sign convention follows exp[i(k z + m theta + omega t)].  The experimental
    comparison usually uses positive measured frequency, so callers commonly compare
    absolute frequencies when matching the long-wave branch.
    """
    if a0 <= 0 or m == 0:
        raise ValueError("a0>0 and m!=0 required")
    Omega0 = gamma / (2.0 * math.pi * a0 * a0)
    x = a0 * abs(k)
    if x <= 0:
        return complex(omega)
    tw = complex(omega + m * Omega0 - k * vz)
    if abs(tw) < 1e-14 * max(1.0, abs(Omega0)):
        return complex(np.inf)
    den0 = 4.0 * Omega0 * Omega0 - tw * tw
    if abs(den0) < 1e-14 * max(1.0, Omega0 * Omega0):
        return complex(np.inf)
    beta = complex(k) * np.sqrt(4.0 * Omega0 * Omega0 / (tw * tw) - 1.0 + 0j)
    z = beta * a0
    J = jv(abs(m), z)
    if abs(J) < 1e-14:
        return complex(np.inf)
    jp = jvp(abs(m), z, 1)
    K = kv(abs(m), x)
    kp = kvp(abs(m), x, 1)
    if not np.isfinite(K) or K == 0:
        return complex(np.inf)
    lhs = ((omega + m * Omega0) ** 2 / den0) * (z * jp / J + 2.0 * Omega0 * m / tw)
    rhs = -x * kp / K
    return complex(lhs - rhs)


def rankine_roots(k: float, *, a0: float, gamma: float, vz: float, m: int = 1,
                   omega_span: float = 6.0, scan_points: int = 3500) -> list[float]:
    Omega0 = gamma / (2.0 * math.pi * a0 * a0)
    grid = np.linspace(-omega_span * Omega0, omega_span * Omega0, int(scan_points))
    roots: list[float] = []
    prev_w: float | None = None
    prev_r: float | None = None
    for w in grid:
        z = rankine_residual(float(w), float(k), a0=a0, gamma=gamma, vz=vz, m=m)
        if not np.isfinite(z.real) or abs(z.imag) > 1e-5 * max(1.0, abs(z.real)) or abs(z.real) > 1e8:
            prev_w = prev_r = None
            continue
        r = float(z.real)
        if prev_r is not None and r * prev_r < 0.0:
            try:
                rr = brentq(lambda q: rankine_residual(q, float(k), a0=a0, gamma=gamma, vz=vz, m=m).real,
                            float(prev_w), float(w), maxiter=120)
                if all(abs(rr - old) > 1e-5 * max(abs(Omega0), 1.0) for old in roots):
                    res = rankine_residual(rr, float(k), a0=a0, gamma=gamma, vz=vz, m=m)
                    if abs(res) < 1e-5:
                        roots.append(float(rr))
            except Exception:
                pass
        prev_w, prev_r = float(w), r
    return roots


def rankine_bending_branch(x_values: Iterable[float], *, a0: float = 1.47e-3,
                            gamma: float = 0.018, vz: float = -0.63,
                            m: int = 1, scan_points: int = 3500) -> list[dict[str, float]]:
    """Track the m=1 branch by selecting the smallest-|omega| real root at each x."""
    Omega0 = gamma / (2.0 * math.pi * a0 * a0)
    rows: list[dict[str, float]] = []
    for x in x_values:
        k = float(x) / a0
        roots = rankine_roots(k, a0=a0, gamma=gamma, vz=vz, m=m, scan_points=scan_points)
        if not roots:
            rows.append({"x": float(x), "k_m_inv": k, "root_found": 0.0})
            continue
        w = min(roots, key=abs)
        w_lw = float(long_wave_omega(np.array([k]), a0, gamma)[0])
        w_hi = k * vz + Omega0
        res = rankine_residual(w, k, a0=a0, gamma=gamma, vz=vz, m=m)
        rows.append({
            "x": float(x), "k_m_inv": k, "root_found": 1.0,
            "omega_rad_s": float(w), "abs_omega_over_Omega0": abs(w) / Omega0,
            "long_wave_abs_over_Omega0": abs(w_lw) / Omega0,
            "high_k_abs_over_Omega0": abs(w_hi) / Omega0,
            "residual_abs": abs(res),
        })
    return rows


def make_ring(n: int, radius: float = 1.0) -> np.ndarray:
    th = np.linspace(0.0, 2.0 * math.pi, int(n), endpoint=False)
    return np.column_stack((radius * np.cos(th), radius * np.sin(th), np.zeros_like(th)))


def ring_frame(n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    th = np.linspace(0.0, 2.0 * math.pi, int(n), endpoint=False)
    t = np.column_stack((-np.sin(th), np.cos(th), np.zeros_like(th)))
    normal = np.column_stack((np.cos(th), np.sin(th), np.zeros_like(th)))
    binormal = np.tile(np.array([[0.0, 0.0, 1.0]]), (int(n), 1))
    return th, t, normal, binormal


def ring_helical_basis(n: int, mode: int, helicity: int = 1) -> tuple[np.ndarray, np.ndarray]:
    if mode < 1 or helicity not in {-1, 1}:
        raise ValueError("mode>=1 and helicity=+/-1 required")
    th, _, normal, binormal = ring_frame(n)
    c = np.cos(mode * th); s = np.sin(mode * th)
    # real/imag parts of (normal + i h binormal) exp(i m theta)
    e_re = c[:, None] * normal - helicity * s[:, None] * binormal
    e_im = s[:, None] * normal + helicity * c[:, None] * binormal
    # RMS-normalize so amplitude is geometrically interpretable.
    e_re /= math.sqrt(float(np.mean(np.sum(e_re * e_re, axis=1))))
    e_im /= math.sqrt(float(np.mean(np.sum(e_im * e_im, axis=1))))
    return e_re, e_im


def single_rhs_hat(curve: np.ndarray, *, radius: float, gamma: float, eps_over_R: float,
                   backend: Any, remove_tangential_gauge: bool = True) -> np.ndarray:
    x = np.ascontiguousarray(curve, dtype=float)
    eps = float(eps_over_R) * float(radius)
    v = np.asarray(backend.induced_velocity(x, x, float(gamma), eps), dtype=float)
    if remove_tangential_gauge:
        chord = np.roll(x, -1, axis=0) - np.roll(x, 1, axis=0)
        t = chord / np.maximum(np.linalg.norm(chord, axis=1)[:, None], 1e-30)
        v -= np.einsum("ij,ij->i", v, t)[:, None] * t
    omega_scale = abs(float(gamma)) / (4.0 * math.pi * radius * radius)
    return v / max(omega_scale, 1e-30)


def ring_linear_mode(mode: int, *, n: int = 64, radius: float = 1.0,
                     eps_over_R: float = 0.05, fd_step_over_R: float = 1e-5,
                     gamma: float = 1.0, force_python: bool = False,
                     skip_build: bool = False) -> dict[str, Any]:
    """Finite-difference 2x2 helical subspace of the regularized Biot--Savart ring Jacobian."""
    backend, bname = load_backend(force_python=force_python, skip_build=skip_build)
    x0 = make_ring(n, radius)
    e1, e2 = ring_helical_basis(n, mode, helicity=1)
    h = fd_step_over_R * radius
    rhs = lambda x: single_rhs_hat(x, radius=radius, gamma=gamma, eps_over_R=eps_over_R, backend=backend)
    Y = []
    for e in (e1, e2):
        y = (rhs(x0 + h * e) - rhs(x0 - h * e)) / (2.0 * h)
        # remove perturbation of the global translation mode by subtracting centroid velocity
        y = y - y.mean(axis=0)
        Y.append(y)
    B = np.column_stack((e1.reshape(-1), e2.reshape(-1)))
    gram = B.T @ B
    G = np.zeros((2, 2), dtype=float)
    for j, y in enumerate(Y):
        G[:, j] = np.linalg.solve(gram, B.T @ y.reshape(-1))
    vals = np.linalg.eigvals(G)
    idx = int(np.argmax(np.abs(vals.imag)))
    lam = complex(vals[idx])
    return {
        "mode": int(mode), "backend": bname, "generator": G,
        "eigenvalues": vals, "lambda_selected": lam,
        "omega_hat": abs(float(lam.imag)),
        "growth_hat": float(lam.real),
        "quality_re_over_im": abs(float(lam.real)) / max(abs(float(lam.imag)), 1e-30),
        "gram_condition": float(np.linalg.cond(gram)),
    }


def perturb_ring(base: np.ndarray, amplitudes: dict[int, complex], *, helicity: int = 1) -> np.ndarray:
    x = np.asarray(base, dtype=float).copy()
    for m, amp in amplitudes.items():
        e_re, e_im = ring_helical_basis(len(base), int(m), helicity=helicity)
        x += float(np.real(amp)) * e_re - float(np.imag(amp)) * e_im
    return x


def ring_modal_amplitudes(curve: np.ndarray, base: np.ndarray, modes: Iterable[int]) -> dict[int, complex]:
    """Project a near-ring state onto fixed helical quadratures after removing centroid translation."""
    x = np.asarray(curve, dtype=float)
    b = np.asarray(base, dtype=float)
    # Translation is the exact relative motion of an ideal ring.  We deliberately do
    # not Kabsch-rotate here, because an axial rotation would erase Kelvin phase.
    x = x - (x.mean(axis=0) - b.mean(axis=0))
    dx = x - b
    out: dict[int, complex] = {}
    for m in modes:
        e_re, e_im = ring_helical_basis(len(base), int(m), helicity=1)
        nr = float(np.sum(e_re * e_re)); ni = float(np.sum(e_im * e_im))
        qr = float(np.sum(dx * e_re) / nr)
        qi = -float(np.sum(dx * e_im) / ni)
        out[int(m)] = complex(qr, qi)
    return out


def simulate_ring_modes(*, n: int, modes: Iterable[int], initial_amplitudes: dict[int, complex],
                        radius: float = 1.0, eps_over_R: float = 0.05, gamma: float = 1.0,
                        dt_hat: float = 0.002, time_hat: float = 0.8, sample_stride: int = 2,
                        force_python: bool = False, skip_build: bool = False) -> dict[str, Any]:
    backend, bname = load_backend(force_python=force_python, skip_build=skip_build)
    base = make_ring(n, radius)
    x = perturb_ring(base, initial_amplitudes)
    modes = sorted(set(int(m) for m in modes))
    rhs = lambda q: single_rhs_hat(q, radius=radius, gamma=gamma, eps_over_R=eps_over_R, backend=backend)
    times: list[float] = []
    series = {m: [] for m in modes}
    energy_proxy: list[float] = []
    nsteps = int(math.ceil(time_hat / dt_hat))
    for step in range(nsteps + 1):
        if step % sample_stride == 0:
            t = step * dt_hat
            aa = ring_modal_amplitudes(x, base, modes)
            times.append(t)
            for m in modes:
                series[m].append(aa[m])
            energy_proxy.append(float(sum((m * m) * abs(aa[m]) ** 2 for m in modes)))
        if step == nsteps:
            break
        x = rk4_step(x, dt_hat, rhs)
        if not np.all(np.isfinite(x)):
            raise RuntimeError("non-finite ring state")
    return {
        "backend": bname,
        "times": np.asarray(times, dtype=float),
        "modes": modes,
        "amplitudes": {m: np.asarray(series[m], dtype=complex) for m in modes},
        "energy_proxy": np.asarray(energy_proxy, dtype=float),
        "terminal_curve": x,
    }


def phase_slope(times: np.ndarray, z: np.ndarray, *, min_fraction: float = 0.15) -> dict[str, float]:
    t = np.asarray(times, dtype=float); a = np.asarray(z, dtype=complex)
    amp = np.abs(a)
    mask = amp > max(np.max(amp) * min_fraction, 1e-14)
    if np.sum(mask) < 5:
        return {"omega_hat": float("nan"), "phase_rms": float("nan"), "amp_mean": float(np.mean(amp))}
    ph = np.unwrap(np.angle(a[mask]))
    tt = t[mask]
    p = np.polyfit(tt, ph, 1)
    fit = p[0] * tt + p[1]
    return {
        "omega_hat": float(p[0]),
        "phase_rms": float(np.sqrt(np.mean((ph - fit) ** 2))),
        "amp_mean": float(np.mean(amp[mask])),
    }


def enumerate_resonances(freqs: dict[int, float], order: int, *, top_n: int = 50) -> list[dict[str, Any]]:
    """Enumerate 2<->2 or 3<->3 resonances with integer mode conservation.

    Trivial resonances in which the incoming and outgoing multisets are identical are removed.
    """
    if order not in {4, 6}:
        raise ValueError("order must be 4 or 6")
    modes = sorted(int(m) for m in freqs)
    half = order // 2
    groups = list(itertools.combinations_with_replacement(modes, half))
    by_sum: dict[int, list[tuple[int, ...]]] = {}
    for g in groups:
        by_sum.setdefault(sum(g), []).append(g)
    rows: list[dict[str, Any]] = []
    for s, gs in by_sum.items():
        for ia, a in enumerate(gs):
            for b in gs[ia + 1:]:
                if tuple(sorted(a)) == tuple(sorted(b)):
                    continue
                wa = sum(freqs[m] for m in a); wb = sum(freqs[m] for m in b)
                det = float(wa - wb)
                scale = max(0.5 * (abs(wa) + abs(wb)), 1e-30)
                rows.append({
                    "order": order, "incoming": list(a), "outgoing": list(b),
                    "mode_sum": int(s), "detuning_hat": det,
                    "relative_detuning": abs(det) / scale,
                })
    rows.sort(key=lambda r: r["relative_detuning"])
    return rows[: int(top_n)]
