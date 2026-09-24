"""Preregistered Biot–Savart tube-field bridge P_BS."""

from __future__ import annotations

from typing import Any

import numpy as np

from .backend import load_backend
from .geometry import bishop_frame, polygon_length
from .kelvin import make_ring, perturb_ring
from .measure import weighted_inner
from .paths import load_thresholds


def c006_hat_to_a029_time(t_hat, *, R_eff: float, a_core: float) -> np.ndarray:
    if a_core <= 0:
        raise ValueError("core radius must be positive")
    return np.asarray(t_hat, dtype=float) * 2.0 * (float(R_eff) / float(a_core)) ** 2


def k_closed(n: int, m: int, theta_B: float, L_hat: float) -> float:
    return (2.0 * np.pi * float(n) - float(m) * float(theta_B)) / max(float(L_hat), 1e-14)


def tube_targets(X_ref, r, theta, *, a, tangent, normal, binormal) -> np.ndarray:  # noqa: ARG001
    X_ref = np.asarray(X_ref, dtype=float)
    r = np.asarray(r, dtype=float)
    theta = np.asarray(theta, dtype=float)
    pts = []
    for j in range(len(X_ref)):
        for th in theta:
            er = np.cos(th) * normal[j] + np.sin(th) * binormal[j]
            for ri in r:
                pts.append(X_ref[j] + float(a) * float(ri) * er)
    return np.ascontiguousarray(pts, dtype=float)


def cartesian_to_tube(u, theta, *, tangent, normal, binormal) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    u = np.asarray(u, dtype=float).reshape(len(tangent), len(theta), -1, 3)
    ur = np.empty(u.shape[:3], dtype=float)
    ut = np.empty_like(ur)
    us = np.empty_like(ur)
    for j in range(u.shape[0]):
        for k, th in enumerate(theta):
            er = np.cos(th) * normal[j] + np.sin(th) * binormal[j]
            eth = -np.sin(th) * normal[j] + np.cos(th) * binormal[j]
            ur[j, k] = u[j, k] @ er
            ut[j, k] = u[j, k] @ eth
            us[j, k] = u[j, k] @ tangent[j]
    return ur, ut, us


def fourier_radial(field, *, m: int, k_hat: float, a: float, L: float) -> np.ndarray:
    """Project (s, theta, r) field onto e^{i(m θ + k_hat s/a)}."""
    ns, ntheta, _nr = field.shape
    theta = np.linspace(0.0, 2.0 * np.pi, ntheta, endpoint=False)
    s = np.arange(ns) * (float(L) / ns)
    phase = np.exp(-1j * (int(m) * theta[None, :] + float(k_hat) * s[:, None] / float(a)))
    return np.mean(field * phase[:, :, None], axis=(0, 1))


def apply_p_bs(X, X_ref, *, a, r, n_theta, gamma, eps, backend) -> dict[str, Any]:
    X = np.asarray(X, dtype=float)
    X_ref = np.asarray(X_ref, dtype=float)
    tangent, normal, binormal = bishop_frame(X_ref)
    theta = np.linspace(0.0, 2.0 * np.pi, int(n_theta), endpoint=False)
    targets = tube_targets(X_ref, r, theta, a=a, tangent=tangent, normal=normal, binormal=binormal)
    u = np.asarray(backend.induced_velocity(targets, X, float(gamma), float(eps)), dtype=float)
    u0 = np.asarray(backend.induced_velocity(targets, X_ref, float(gamma), float(eps)), dtype=float)
    du = (u - u0).reshape(len(X_ref), len(theta), len(r), 3)
    ur, ut, us = cartesian_to_tube(du, theta, tangent=tangent, normal=normal, binormal=binormal)
    return {
        "ur": ur,
        "ut": ut,
        "us": us,
        "targets": targets,
        "tangent": tangent,
        "normal": normal,
        "binormal": binormal,
        "theta": theta,
    }


def modal_coefficient(field, sealed: dict[str, Any], *, m: int, k_hat: float, a: float, L: float) -> complex:
    ur = fourier_radial(field["ur"], m=m, k_hat=k_hat, a=a, L=L)
    ut = fourier_radial(field["ut"], m=m, k_hat=k_hat, a=a, L=L)
    us = fourier_radial(field["us"], m=m, k_hat=k_hat, a=a, L=L)
    nr = ur.size
    u_vec = np.zeros(4 * nr, dtype=complex)
    u_vec[:nr] = ur
    u_vec[nr : 2 * nr] = ut
    u_vec[2 * nr : 3 * nr] = us
    return weighted_inner(sealed["p"], u_vec, sealed["W"], sealed["B"])


def diagnostic_right_overlap(field, sealed: dict[str, Any], *, m: int, k_hat: float, a: float, L: float) -> complex:
    ur = fourier_radial(field["ur"], m=m, k_hat=k_hat, a=a, L=L)
    ut = fourier_radial(field["ut"], m=m, k_hat=k_hat, a=a, L=L)
    us = fourier_radial(field["us"], m=m, k_hat=k_hat, a=a, L=L)
    nr = ur.size
    u_vec = np.zeros(4 * nr, dtype=complex)
    u_vec[:nr] = ur
    u_vec[nr : 2 * nr] = ut
    u_vec[2 * nr : 3 * nr] = us
    q = sealed["q"]
    return weighted_inner(q, u_vec, sealed["W"], sealed["B"]) / max(abs(weighted_inner(q, q, sealed["W"], sealed["B"])), 1e-30)


def divergence_diagnostic(field, r) -> float:
    ur = np.mean(field["ur"], axis=(0, 1))
    r = np.asarray(r, dtype=float)
    re = r.copy()
    re[0] = max(0.5 * r[1], 1e-10)
    dur = np.gradient(re * ur, re)
    div = np.abs(dur / re)
    scale = max(float(np.max(np.abs(ur))), 1e-12)
    return float(np.max(div) / scale)


def subspace_overlap(field, _r=None) -> float:
    ur = np.mean(np.abs(field["ur"]), axis=(0, 1))
    ut = np.mean(np.abs(field["ut"]), axis=(0, 1))
    us = np.mean(np.abs(field["us"]), axis=(0, 1))
    tot = float(np.sum(ur + ut + us))
    interior = float(np.sum((ur + ut + us)[:-1]))
    return interior / max(tot, 1e-30)


def p_of_zero(X_ref, **kwargs) -> dict[str, Any]:
    field = apply_p_bs(X_ref, X_ref, **kwargs)
    amp = float(np.max(np.abs(field["ur"])) + np.max(np.abs(field["ut"])) + np.max(np.abs(field["us"])))
    return {"ok": amp <= 1e-12, "amp": amp, "field": field}


def linearity_check(X_ref, *, amplitude: float = 1e-3, **kwargs) -> dict[str, Any]:
    dx = perturb_ring(X_ref, {1: amplitude})
    dx2 = perturb_ring(X_ref, {1: 2.0 * amplitude})
    f1 = apply_p_bs(dx, X_ref, **kwargs)
    f2 = apply_p_bs(dx2, X_ref, **kwargs)
    num = np.linalg.norm((2.0 * f1["ur"] - f2["ur"]).ravel())
    den = max(np.linalg.norm(f2["ur"].ravel()), 1e-30)
    rel = float(num / den)
    return {"ok": rel < 0.25, "relative_error": rel}


def qualify_p(sealed: dict[str, Any], thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
    thr = thresholds or load_thresholds()
    backend, _name = load_backend(force_python=True, skip_build=True)
    ring = make_ring(int(thr["ring"]["N"]), float(thr["ring"]["R"]))
    a = float(thr["ring"]["eps_over_R"]) * float(thr["ring"]["R"])
    r = sealed["r"]
    kwargs = dict(
        a=a,
        r=r,
        n_theta=int(thr["n_theta"]),
        gamma=float(thr["ring"]["gamma"]),
        eps=a,
        backend=backend,
    )
    zero = p_of_zero(ring, **kwargs)
    lin = linearity_check(ring, **kwargs)
    pert = perturb_ring(ring, {1: 1e-3})
    field = apply_p_bs(pert, ring, **kwargs)
    L = polygon_length(ring)
    Lhat = L / a
    khat = k_closed(int(thr["ring"]["n"]), int(thr["ring"]["m"]), 0.0, Lhat)
    if r.size != sealed["q"].size // 4:
        return {"ok": False, "reason": "radial grid mismatch", "zero": zero, "linearity": lin}
    a_m = modal_coefficient(field, sealed, m=int(thr["ring"]["m"]), k_hat=khat, a=a, L=L)
    div = divergence_diagnostic(field, r)
    overlap = subspace_overlap(field, r)
    tests = {
        "p_of_zero": zero["ok"],
        "linearity": lin["ok"],
        "subspace_overlap": overlap >= float(thr["subspace_overlap_min"]),
        "finite_amplitude": np.isfinite(a_m),
    }
    return {
        "ok": all(tests.values()),
        "tests": tests,
        "a_m": {"real": float(a_m.real), "imag": float(a_m.imag)},
        "divergence_proxy": div,
        "subspace_overlap": overlap,
        "zero": {"amp": zero["amp"]},
        "linearity": {"relative_error": lin["relative_error"]},
        "prediction_inputs_consumed": [],
    }
