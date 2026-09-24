import numpy as np
from .spectral import derivative_axis

def metric_derivatives(g, L):
    out = [np.zeros_like(g)]  # static: d/dt = 0
    for axis in range(3):
        out.append(derivative_axis(g, axis, L))
    return out

def christoffel(g, L):
    inv = np.linalg.inv(g)
    dg = metric_derivatives(g, L)
    shape = g.shape[:-2]
    Gamma = np.zeros(shape + (4, 4, 4), dtype=float)
    for a in range(4):
        for b in range(4):
            for c in range(4):
                acc = np.zeros(shape, dtype=float)
                for d in range(4):
                    acc += inv[..., a, d] * (
                        dg[b][..., d, c]
                        + dg[c][..., d, b]
                        - dg[d][..., b, c]
                    )
                Gamma[..., a, b, c] = 0.5 * acc
    return Gamma

def riemann(g, L):
    Gamma = christoffel(g, L)
    dGamma = [np.zeros_like(Gamma)]
    for axis in range(3):
        dGamma.append(derivative_axis(Gamma, axis, L))

    shape = g.shape[:-2]
    R = np.zeros(shape + (4, 4, 4, 4), dtype=float)
    for a in range(4):
        for b in range(4):
            for c in range(4):
                for d in range(4):
                    val = dGamma[c][..., a, b, d] - dGamma[d][..., a, b, c]
                    for e in range(4):
                        val += (
                            Gamma[..., a, e, c] * Gamma[..., e, b, d]
                            - Gamma[..., a, e, d] * Gamma[..., e, b, c]
                        )
                    R[..., a, b, c, d] = val
    return R

def curvature_diagnostics(g, L):
    eig = np.linalg.eigvalsh(g.reshape((-1, 4, 4)))
    negative_counts = np.sum(eig < 0.0, axis=1)

    R = riemann(g, L)
    curvature_rms = float(np.sqrt(np.mean(R * R)))

    Rlow = np.einsum("...ae,...ebcd->...abcd", g, R)
    # swap antisymmetric index pairs: (a,b,c,d) -> (c,d,a,b)
    Rpair = np.transpose(Rlow, (0, 1, 2, 5, 6, 3, 4))
    denom = float(np.linalg.norm(Rlow.ravel()))
    pair_rel = 0.0 if denom == 0.0 else float(
        np.linalg.norm((Rlow - Rpair).ravel()) / denom
    )
    return {
        "metric_negative_eigs_min": int(negative_counts.min()),
        "metric_negative_eigs_max": int(negative_counts.max()),
        "metric_eig_min": float(eig.min()),
        "metric_eig_max": float(eig.max()),
        "curvature_rms": curvature_rms,
        "riemann_pair_rel_l2": pair_rel,
    }
