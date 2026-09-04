from __future__ import annotations
import numpy as np
from .kernels import velocity
from .geometry import split_components, pack


def _tangent_field(points, offsets):
    fields = []
    for C in split_components(np.asarray(points, float), offsets):
        d = np.roll(C, -1, axis=0) - np.roll(C, 1, axis=0)
        n = np.linalg.norm(d, axis=1)
        if np.any(n <= 1e-15):
            raise RuntimeError("degenerate tangent in relative-equilibrium fit")
        fields.append(d / n[:, None])
    return pack(fields)[0]


def _rigid_matrix(x):
    xx, yy, zz = x
    # U + Omega x x = U - [x]_x Omega
    return np.array([
        [1, 0, 0, 0, zz, -yy],
        [0, 1, 0, -zz, 0, xx],
        [0, 0, 1, yy, -xx, 0],
    ], float)


def _fit_full(X, V):
    A = np.vstack([_rigid_matrix(x) for x in X])
    b = np.concatenate(V)
    q = np.linalg.lstsq(A, b, rcond=None)[0]
    pred = (A @ q).reshape(-1, 3)
    res = float(np.linalg.norm(V - pred) / max(np.linalg.norm(V), 1e-300))
    return q, pred, res


def _fit_normal(X, V, tangent):
    rows = []
    rhs = []
    I = np.eye(3)
    for x, v, t in zip(X, V, tangent):
        P = I - np.outer(t, t)
        M = _rigid_matrix(x)
        rows.append(P @ M)
        rhs.append(P @ v)
    A = np.vstack(rows)
    b = np.concatenate(rhs)
    q = np.linalg.lstsq(A, b, rcond=None)[0]
    pred = np.vstack([_rigid_matrix(x) @ q for x in X])
    Vn = V - np.sum(V * tangent, axis=1)[:, None] * tangent
    R = V - pred
    Rn = R - np.sum(R * tangent, axis=1)[:, None] * tangent
    res = float(np.linalg.norm(Rn) / max(np.linalg.norm(Vn), 1e-300))
    return q, pred, res, float(np.linalg.norm(Vn))


def fit_relative_equilibrium(points, offsets, gamma, core, require_native=False):
    """Return both material/full and centerline-normal relative-equilibrium residuals.

    For an unlabelled centerline, tangential marker velocity is a parametrization
    degree of freedom.  v0.3.1 therefore gates the action carrier on the projected
    normal residual epsilon_RE_perp while retaining epsilon_RE_full as a separate
    material-marker diagnostic.
    """
    X = np.asarray(points, float)
    V = velocity(X, offsets, gamma, core, require_native)
    t = _tangent_field(X, offsets)

    qf, predf, full_res = _fit_full(X, V)
    qn, predn, perp_res, normal_norm = _fit_normal(X, V, t)
    full_norm = float(np.linalg.norm(V))

    return {
        "U": qn[:3].tolist(),
        "Omega": qn[3:].tolist(),
        "U_full_fit": qf[:3].tolist(),
        "Omega_full_fit": qf[3:].tolist(),
        "epsilon_RE": perp_res,
        "epsilon_RE_perp": perp_res,
        "epsilon_RE_full": full_res,
        "velocity_norm": full_norm,
        "normal_velocity_norm": normal_norm,
        "normal_velocity_fraction": normal_norm / max(full_norm, 1e-300),
        "gate_definition": "normal_projected_centerline_relative_equilibrium",
    }
