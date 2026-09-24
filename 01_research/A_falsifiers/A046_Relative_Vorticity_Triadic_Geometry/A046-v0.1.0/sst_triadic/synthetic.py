import numpy as np
from .spectral import grad_scalar

def abc_flow(n, L):
    x = np.linspace(0.0, L, n, endpoint=False)
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    u = np.empty((n, n, n, 3), dtype=float)
    u[..., 0] = np.sin(Z) + np.cos(Y)
    u[..., 1] = np.sin(X) + np.cos(Z)
    u[..., 2] = np.sin(Y) + np.cos(X)
    return u

def taylor_green(n, L):
    x = np.linspace(0.0, L, n, endpoint=False)
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    u = np.empty((n, n, n, 3), dtype=float)
    u[..., 0] = np.sin(X) * np.cos(Y) * np.cos(Z)
    u[..., 1] = -np.cos(X) * np.sin(Y) * np.cos(Z)
    u[..., 2] = 0.0
    return u

def shear_wave(n, L):
    x = np.linspace(0.0, L, n, endpoint=False)
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    u = np.zeros((n, n, n, 3), dtype=float)
    u[..., 0] = np.sin(Y) + 0.2 * np.sin(2.0 * Z)
    return u

def localized_vortex(n, L, sigma=0.70):
    x = np.linspace(-L / 2.0, L / 2.0, n, endpoint=False)
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    psi = np.exp(-(X * X + Y * Y + Z * Z) / (2.0 * sigma * sigma))
    gp = grad_scalar(psi, L)
    u = np.zeros((n, n, n, 3), dtype=float)
    u[..., 0] = gp[..., 1]
    u[..., 1] = -gp[..., 0]
    return u

def uniform_flow(n, vector=(0.15, -0.10, 0.05)):
    u = np.zeros((n, n, n, 3), dtype=float)
    u[...] = np.asarray(vector, dtype=float)
    return u
