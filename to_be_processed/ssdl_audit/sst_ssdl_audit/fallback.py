from __future__ import annotations

import math
from typing import Any, Dict

import numpy as np


def run_ssdl_numpy(R: float, n_theta: int, n_phi: int) -> Dict[str, Any]:
    N = n_theta * n_phi
    theta = np.linspace(0, math.pi, n_theta, endpoint=False) + math.pi / (2 * n_theta)
    phi = np.linspace(0, 2 * math.pi, n_phi, endpoint=False) + math.pi / n_phi
    T, P = np.meshgrid(theta, phi, indexing="ij")

    x = R * np.sin(T) * np.cos(P)
    y = R * np.sin(T) * np.sin(P)
    z = R * np.cos(T)
    pts = np.column_stack((x.ravel(), y.ravel(), z.ravel()))

    d_theta = math.pi / n_theta
    d_phi = 2 * math.pi / n_phi
    areas = (R * R * np.sin(T) * d_theta * d_phi).ravel()

    # Dirichlet Condition met extreme tangentiële verstoring
    phi_input = 1.0 + 0.5 * np.cos(T) + 0.2 * np.sin(T) * np.cos(P)
    phi_input = phi_input.ravel()

    # BEM Matrix
    diff = pts[:, np.newaxis, :] - pts[np.newaxis, :, :]
    dists = np.linalg.norm(diff, axis=2)
    np.fill_diagonal(dists, 1.0)
    V = areas[np.newaxis, :] / (4.0 * math.pi * dists)
    np.fill_diagonal(V, np.sqrt(areas / math.pi) / 2.0)

    sigma = np.linalg.solve(V, phi_input)

    # Monopool Projecties Pi_0
    total_area = np.sum(areas)
    phi_0 = np.sum(phi_input * areas) / total_area
    sigma_0 = np.sum(sigma * areas) / total_area

    R_num = phi_0 / sigma_0

    return {
        "backend": "numpy",
        "R_target": float(R),
        "R_numerical_projected": float(R_num),
        "projection_error": float(abs(R_num - R) / R),
        "phi_0_monopole": float(phi_0),
        "sigma_0_monopole": float(sigma_0),
    }
