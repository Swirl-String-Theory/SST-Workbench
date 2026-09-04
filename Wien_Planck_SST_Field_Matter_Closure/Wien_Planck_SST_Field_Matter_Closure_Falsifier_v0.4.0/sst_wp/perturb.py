from __future__ import annotations
import numpy as np
from .geometry import split_components, pack, total_length


def _component_tangents(c):
    d = np.roll(c, -1, axis=0) - np.roll(c, 1, axis=0)
    n = np.linalg.norm(d, axis=1)
    if np.any(n <= 1e-15):
        raise RuntimeError("degenerate tangent in perturbation geometry")
    return d / n[:, None]


def tangent_field(points, offsets):
    fields = [_component_tangents(c) for c in split_components(np.asarray(points, float), offsets)]
    return pack(fields)[0]


def normal_field(points, offsets, harmonics=(1, 2, 3, 4)):
    comps = split_components(points, offsets)
    fields = []
    for C in comps:
        n = len(C)
        t = _component_tangents(C)
        g = np.array([0.0, 0.0, 1.0])
        N = g - (t @ g)[:, None] * t
        bad = np.linalg.norm(N, axis=1) < 1e-6
        if np.any(bad):
            g2 = np.array([0.0, 1.0, 0.0])
            N[bad] = g2 - (t[bad] @ g2)[:, None] * t[bad]
        N /= np.maximum(np.linalg.norm(N, axis=1)[:, None], 1e-15)
        s = np.arange(n) / n
        amp = np.zeros(n)
        for h in harmonics:
            amp += np.sin(2 * np.pi * h * s + 0.37 * h) / len(harmonics)
        fields.append(N * amp[:, None])
    return pack(fields)[0]


def project_mode_to_normal(points, offsets, mode_flat, normalize_rms=True):
    """Project a frozen flattened mode into the centerline normal bundle.

    Tangential marker motion is a centerline parametrization/gauge degree of
    freedom.  The matched action branch therefore perturbs only the normal
    component of a mode discovered from an independent probe trajectory.
    """
    X = np.asarray(points, float)
    M = np.asarray(mode_flat, float).reshape(X.shape).copy()
    t = tangent_field(X, offsets)
    full_norm = float(np.linalg.norm(M))
    M -= np.sum(M * t, axis=1)[:, None] * t
    normal_norm = float(np.linalg.norm(M))
    normal_fraction = normal_norm / max(full_norm, 1e-300)
    rms = float(np.sqrt(np.mean(np.sum(M * M, axis=1))))
    if not np.isfinite(rms) or rms <= 1e-14:
        raise RuntimeError("discovered mode has negligible normal content")
    if normalize_rms:
        M /= rms
    return M.reshape(-1), {
        "mode_normal_fraction": float(normal_fraction),
        "mode_normal_rms_before_normalization": rms,
        "mode_rms_after_normalization": float(np.sqrt(np.mean(np.sum(M * M, axis=1)))),
    }


def _fixed_length_shape(points, offsets):
    X = np.asarray(points, float).copy()
    X = X - X.mean(0)
    comps = split_components(X, offsets)
    L = total_length(comps)
    if not np.isfinite(L) or L <= 0:
        raise RuntimeError("invalid total length after perturbation")
    return X / L


def perturbed(points, offsets, eps, sign=1):
    """Legacy broadband normal probe, retained only for mode discovery."""
    F = normal_field(points, offsets)
    X = np.asarray(points, float) + sign * float(eps) * F
    return _fixed_length_shape(X, offsets)


def perturbed_along_mode(points, offsets, mode_flat, eps, sign=1):
    """Matched +/- perturbation along one already-frozen normal mode."""
    X = np.asarray(points, float)
    M = np.asarray(mode_flat, float).reshape(X.shape)
    Y = X + sign * float(eps) * M
    return _fixed_length_shape(Y, offsets)
