import math
import numpy as np

from .filaments import hopf_cell, quasi_uniform_rotations, rotate_cell


def _grid_points(grid):
    x = np.arange(grid.n, dtype=float) * grid.length / grid.n
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    return np.stack((X, Y, Z), axis=-1)


def _periodic_delta(a, b, length):
    d = np.asarray(a) - np.asarray(b)
    L = float(length)
    return (d + 0.5 * L) % L - 0.5 * L


def _centers_from_grid(shape, length):
    nx, ny, nz = [int(v) for v in shape]
    out = []
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                out.append(np.array([
                    (i + 0.5) * length / nx,
                    (j + 0.5) * length / ny,
                    (k + 0.5) * length / nz,
                ], dtype=float))
    return out


def structured_hopf_tube_background(grid, cfg, seed=0):
    """Construct a smooth periodic vorticity field from an isotropically oriented Hopf-cell ensemble.

    Each closed filament is deposited as a 3-D Gaussian regularization of
        omega(x) = Gamma * integral delta(x-X(s)) dX(s).
    The deposited vorticity is Helmholtz-projected in Fourier space, and the
    incompressible velocity is recovered from curl u = omega. The entire field
    is finally rescaled to the requested u_rms; the circulation and the blind
    reference speed are scaled by the same factor.
    """
    L = float(grid.length)
    radius = float(cfg["loop_radius"])
    npts = int(cfg["loop_points"])
    sigma = float(cfg["tube_sigma"])
    gamma0 = float(cfg["circulation"])
    target_urms = float(cfg["background_urms"])
    centers = _centers_from_grid(cfg["microcell_grid"], L)
    rots = quasi_uniform_rotations(len(centers), offset=int(seed) % 101 + 17)
    base = hopf_cell(radius=radius, points_per_loop=npts, linked=True)
    pts = _grid_points(grid)
    omega = np.zeros((grid.n, grid.n, grid.n, 3), dtype=float)
    norm = (2.0 * math.pi * sigma * sigma) ** 1.5
    cells = []

    for center, Q in zip(centers, rots):
        cell = rotate_cell(base, Q) + center[None, None, :]
        cell %= L
        cells.append(cell)
        for loop in cell:
            q = np.roll(loop, -1, axis=0)
            dl = _periodic_delta(q, loop, L)
            mid = (loop + 0.5 * dl) % L
            for m, seg in zip(mid, dl):
                d = _periodic_delta(pts, m, L)
                r2 = np.sum(d * d, axis=-1)
                w = np.exp(-0.5 * r2 / (sigma * sigma)) / norm
                omega += gamma0 * w[..., None] * seg[None, None, None, :]

    omega_hat = grid.project(grid.fft(omega))
    safe_k2 = np.where(grid.nonzero, grid.k2, 1.0)
    uhat = 1j * np.cross(grid.kvec, omega_hat) / safe_k2[..., None]
    uhat[~grid.nonzero] = 0.0
    uhat = grid.filter(uhat)
    urms0 = grid.urms(uhat)
    if not np.isfinite(urms0) or urms0 <= 0.0:
        raise RuntimeError("structured vortex-tube background has zero/non-finite velocity")
    scale = target_urms / urms0
    uhat *= scale
    gamma_eff = gamma0 * scale
    vref = abs(gamma_eff) / (2.0 * math.pi * sigma)

    # Geometry-only orientation diagnostic from loop normals.
    normals = []
    for cell in cells:
        for loop in cell:
            q = np.roll(loop, -1, axis=0)
            area = 0.5 * np.sum(np.cross(loop, q), axis=0)
            nrm = np.linalg.norm(area)
            if nrm > 0.0:
                normals.append(area / nrm)
    normals = np.asarray(normals, dtype=float)
    M = (normals.T @ normals) / max(len(normals), 1)
    ori_iso = float(np.linalg.norm(M - np.eye(3) / 3.0))

    return uhat, {
        "microcell_count": len(cells),
        "loop_count": 2 * len(cells),
        "loop_radius": radius,
        "tube_sigma": sigma,
        "circulation_input": gamma0,
        "circulation_effective_after_urms_normalization": gamma_eff,
        "reference_speed": vref,
        "orientation_tensor": M.tolist(),
        "orientation_isotropy_fro": ori_iso,
        "unscaled_urms": urms0,
        "target_urms": target_urms,
        "normalization_scale": scale,
    }


def spectrum_matched_random_control(grid, structured_uhat, seed):
    """Random-phase-like divergence-free control with matched shell energies."""
    rng = np.random.default_rng(int(seed))
    q = grid.filter(grid.project(grid.fft(rng.normal(size=(grid.n, grid.n, grid.n, 3)))))
    kmag = np.sqrt(grid.k2)
    max_shell = int(np.floor(np.max(kmag[grid.dealias])))
    out = np.zeros_like(q)
    for s in range(max_shell + 1):
        shell = (kmag >= s - 0.5) & (kmag < s + 0.5) & grid.dealias
        if not np.any(shell):
            continue
        es = float(np.sum(np.abs(structured_uhat[shell]) ** 2))
        er = float(np.sum(np.abs(q[shell]) ** 2))
        if es > 0.0 and er > 0.0:
            out[shell] = q[shell] * math.sqrt(es / er)
    out = grid.filter(out)
    target = grid.urms(structured_uhat)
    cur = grid.urms(out)
    if cur > 0.0:
        out *= target / cur
    return out


def spectral_edge_fraction(grid, uhat):
    modes = np.fft.fftfreq(grid.n) * grid.n
    mx, my, mz = np.meshgrid(modes, modes, modes, indexing="ij")
    cutoff = grid.n // 3
    edge = np.maximum.reduce([np.abs(mx), np.abs(my), np.abs(mz)]) >= cutoff
    return float(np.sum(np.abs(uhat[edge]) ** 2) / max(np.sum(np.abs(uhat) ** 2), 1e-300))
