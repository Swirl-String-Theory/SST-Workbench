from __future__ import annotations

import math
from typing import Any

import numpy as np


def run_ssdl_numpy(R: float, n_theta: int, n_phi: int) -> dict[str, Any]:
    """Numpy fallback BEM cross-check for the spherical monopole projector.

    This is a numerical consistency check only. The analytic theorem is
    Lambda_{partial,0}^{-1}=R for the exterior spherical monopole sector.
    """
    if R <= 0:
        raise ValueError("R must be positive.")
    if n_theta < 4 or n_phi < 8:
        raise ValueError("mesh too small.")

    theta = np.linspace(0.0, math.pi, n_theta, endpoint=False) + math.pi / (2 * n_theta)
    phi = np.linspace(0.0, 2 * math.pi, n_phi, endpoint=False) + math.pi / n_phi
    T, P = np.meshgrid(theta, phi, indexing="ij")

    x = R * np.sin(T) * np.cos(P)
    y = R * np.sin(T) * np.sin(P)
    z = R * np.cos(T)
    pts = np.column_stack((x.ravel(), y.ravel(), z.ravel()))

    d_theta = math.pi / n_theta
    d_phi = 2 * math.pi / n_phi
    areas = (R * R * np.sin(T) * d_theta * d_phi).ravel()

    # Monopole plus l=1/l=2 tangential contamination.
    phi_input = 1.0 + 0.5 * np.cos(T) + 0.2 * np.sin(T) * np.cos(P) + 0.1 * (3.0 * np.cos(T) ** 2 - 1.0)
    phi_input = phi_input.ravel()

    diff = pts[:, np.newaxis, :] - pts[np.newaxis, :, :]
    dists = np.linalg.norm(diff, axis=2)
    np.fill_diagonal(dists, 1.0)
    V = areas[np.newaxis, :] / (4.0 * math.pi * dists)
    np.fill_diagonal(V, np.sqrt(areas / math.pi) / 2.0)

    sigma = np.linalg.solve(V, phi_input)

    total_area = float(np.sum(areas))
    phi_0 = float(np.sum(phi_input * areas) / total_area)
    sigma_0 = float(np.sum(sigma * areas) / total_area)
    R_num = phi_0 / sigma_0

    return {
        "backend": "numpy_bem",
        "R_target": float(R),
        "R_numerical_projected": float(R_num),
        "projection_error": float(abs(R_num - R) / R),
        "phi_0_monopole": phi_0,
        "sigma_0_monopole": sigma_0,
        "mesh_n_theta": int(n_theta),
        "mesh_n_phi": int(n_phi),
        "interpretation": "BEM consistency check for Pi_0 Lambda^{-1} Pi_0; not a constitutive proof.",
    }
