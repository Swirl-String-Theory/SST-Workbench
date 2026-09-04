# sst_swirl_gravity.py
"""
    # Usage:
    # from sst_swirl_gravity import (
    #     compute_vorticity,
    #     compute_swirl_curvature_tensor,
    #     compute_swirl_gravity,
    # )
    #
    # omega_x, omega_y, omega_z = compute_vorticity(Bx3, By3, Bz3, dx, dy, dz)
    # R_swirl = compute_swirl_curvature_tensor(omega_x, omega_y, omega_z)
    # g = compute_swirl_gravity(omega_x, omega_y, omega_z, R_swirl)

"""


import numpy as np
from typing import Tuple


def compute_vorticity(Bx: np.ndarray,
                      By: np.ndarray,
                      Bz: np.ndarray,
                      dx: float,
                      dy: float,
                      dz: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Vorticity ω = ∇ × B (SST: B als swirl-velocity proxy).
    Bx,By,Bz hebben shape (Nx, Ny, Nz).
    dx,dy,dz zijn grid-afstanden.
    """
    dBz_dy, dBz_dx, dBz_dz = np.gradient(Bz, dy, dx, dz)
    dBy_dz, dBy_dx, dBy_dy = np.gradient(By, dz, dx, dy)
    dBx_dz, dBx_dx, dBx_dy = np.gradient(Bx, dz, dx, dy)

    omega_x = dBy_dz - dBz_dy
    omega_y = dBz_dx - dBx_dz
    omega_z = dBx_dy - dBy_dx
    return omega_x, omega_y, omega_z


def compute_swirl_curvature_tensor(
        omega_x: np.ndarray,
        omega_y: np.ndarray,
        omega_z: np.ndarray,
) -> np.ndarray:
    """
    R_ij = 0.5 * (∂i ω_j + ∂j ω_i)
    Retourneert array met shape (3,3,Nx,Ny,Nz).
    """
    omega = [omega_x, omega_y, omega_z]
    grad_omega = [np.gradient(omega_x), np.gradient(omega_y), np.gradient(omega_z)]

    R_swirl = np.empty((3, 3, *omega_x.shape))
    for i in range(3):
        for j in range(3):
            R_swirl[i, j] = 0.5 * (grad_omega[j][i] + grad_omega[i][j])
    return R_swirl


def compute_swirl_gravity(
        omega_x: np.ndarray,
        omega_y: np.ndarray,
        omega_z: np.ndarray,
        R_swirl: np.ndarray,
) -> np.ndarray:
    """
    g_i = - ω_j R_ij
    omega_*: (Nx,Ny,Nz)
    R_swirl: (3,3,Nx,Ny,Nz)
    Retourneert g met shape (3,Nx,Ny,Nz).
    """
    omega_vec = np.stack([omega_x, omega_y, omega_z], axis=0)  # (3,Nx,Ny,Nz)
    g = np.zeros_like(omega_vec)

    for i in range(3):
        for j in range(3):
            g[i] -= omega_vec[j] * R_swirl[i, j]

    return g