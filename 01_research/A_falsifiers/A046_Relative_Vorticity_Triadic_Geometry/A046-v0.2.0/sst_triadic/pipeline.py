import numpy as np
from .spectral import grad_vector, stress_source, poisson_periodic
from .backend import decompose_gradient


def antisymmetric_from_vorticity(omega):
    omega = np.asarray(omega, dtype=float)
    W = np.zeros(omega.shape[:-1] + (3, 3), dtype=float)
    W[..., 0, 1] = -0.5 * omega[..., 2]
    W[..., 1, 0] = +0.5 * omega[..., 2]
    W[..., 0, 2] = +0.5 * omega[..., 1]
    W[..., 2, 0] = -0.5 * omega[..., 1]
    W[..., 1, 2] = -0.5 * omega[..., 0]
    W[..., 2, 1] = +0.5 * omega[..., 0]
    return W


def reconstruct_velocity_gradient(strain, omega):
    return np.asarray(strain, dtype=float) + antisymmetric_from_vorticity(omega)


def three_layer_response(u, L):
    """
    Explicit v0.2.0 chain:
        u -> (omega, S) -> Q_transport -> Phi_bulk.
    """
    grad = grad_vector(u, L)
    strain, omega_rel, div = decompose_gradient(grad)
    q_transport = stress_source(u, L)
    phi_bulk, lap_phi = poisson_periodic(q_transport, L)
    return {
        "grad": grad,
        "strain": strain,
        "omega_rel": omega_rel,
        "div": div,
        "q_transport": q_transport,
        "phi_bulk": phi_bulk,
        "lap_phi": lap_phi,
    }
