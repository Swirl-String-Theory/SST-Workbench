import numpy as np
from .reference import decompose_gradient, invariants

def rotation_matrix(seed=4501001):
    rng = np.random.default_rng(seed)
    A = rng.normal(size=(3, 3))
    Q, _ = np.linalg.qr(A)
    if np.linalg.det(Q) < 0:
        Q[:, 0] *= -1.0
    return Q

def objectivity_residual(u, grad, seed=4501001):
    S, w, _ = decompose_gradient(grad)
    inv0 = invariants(u, w, S)

    Q = rotation_matrix(seed)
    up = Q @ u
    gradp = Q @ grad @ Q.T
    Sp, wp, _ = decompose_gradient(gradp)
    inv1 = invariants(up, wp, Sp)

    errs = {}
    for k in ["speed2", "omega2", "strain2", "helicity"]:
        a = float(inv0[k])
        b = float(inv1[k])
        errs[k] = abs(a - b) / max(1.0, abs(a), abs(b))
    return max(errs.values()), errs
