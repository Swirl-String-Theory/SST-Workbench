import numpy as np

def decompose_gradient(grad):
    grad = np.asarray(grad, dtype=float)
    S = 0.5 * (grad + np.swapaxes(grad, -1, -2))
    omega = np.stack([
        grad[..., 2, 1] - grad[..., 1, 2],
        grad[..., 0, 2] - grad[..., 2, 0],
        grad[..., 1, 0] - grad[..., 0, 1],
    ], axis=-1)
    div = np.trace(grad, axis1=-2, axis2=-1)
    return S, omega, div

def invariants(u, omega, strain):
    u = np.asarray(u, dtype=float)
    omega = np.asarray(omega, dtype=float)
    strain = np.asarray(strain, dtype=float)
    return {
        "speed2": np.sum(u * u, axis=-1),
        "omega2": np.sum(omega * omega, axis=-1),
        "strain2": np.sum(strain * strain, axis=(-2, -1)),
        "helicity": np.sum(u * omega, axis=-1),
    }

def build_metric(u, omega, strain, c_test, eps_shift, eps_strain, eps_omega2):
    u = np.asarray(u, dtype=float)
    omega = np.asarray(omega, dtype=float)
    strain = np.asarray(strain, dtype=float)

    beta2 = np.sum(u * u, axis=-1) / (c_test * c_test)
    om_rms = float(np.sqrt(np.mean(np.sum(omega * omega, axis=-1))))
    s_rms = float(np.sqrt(np.mean(np.sum(strain * strain, axis=(-2, -1)))))
    if om_rms == 0.0:
        om_rms = 1.0
    if s_rms == 0.0:
        s_rms = 1.0

    g = np.zeros(u.shape[:-1] + (4, 4), dtype=float)
    g[..., 0, 0] = -(1.0 - beta2)

    shift = eps_shift * omega / om_rms
    for i in range(3):
        g[..., 0, i + 1] = shift[..., i]
        g[..., i + 1, 0] = shift[..., i]

    gamma = np.broadcast_to(np.eye(3), u.shape[:-1] + (3, 3)).copy()
    gamma += eps_strain * strain / s_rms

    dyad = np.einsum("...i,...j->...ij", omega, omega) / (om_rms * om_rms)
    om2n = np.sum(omega * omega, axis=-1) / (om_rms * om_rms)
    gamma += eps_omega2 * (
        dyad - om2n[..., None, None] * np.eye(3) / 3.0
    )
    g[..., 1:, 1:] = gamma
    return g

def local_linear_controls(Omega=1.25, a=0.40, radius=0.75):
    grad_A = np.array([
        [0.0, -Omega, 0.0],
        [Omega, 0.0, 0.0],
        [0.0, 0.0, 0.0],
    ])
    grad_B = np.array([
        [a, -Omega, 0.0],
        [Omega, -a, 0.0],
        [0.0, 0.0, 0.0],
    ])
    SA, wA, _ = decompose_gradient(grad_A)
    SB, wB, _ = decompose_gradient(grad_B)
    u0A = np.zeros(3)
    u0B = np.zeros(3)
    hA = float(u0A @ wA)
    hB = float(u0B @ wB)
    GammaA = float(2.0 * np.pi * Omega * radius * radius)
    GammaB = GammaA  # pure strain contributes zero closed-loop circulation
    return {
        "uA": u0A, "uB": u0B,
        "omegaA": wA, "omegaB": wB,
        "strainA": SA, "strainB": SB,
        "hA": hA, "hB": hB,
        "GammaA": GammaA, "GammaB": GammaB,
    }
