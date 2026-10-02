import numpy as np


def fibonacci_sphere(n):
    """Deterministic nearly uniform unit-vector sampling on S^2."""
    n = int(n)
    i = np.arange(n, dtype=float)
    z = 1.0 - 2.0 * (i + 0.5) / n
    golden_angle = np.pi * (3.0 - np.sqrt(5.0))
    phi = i * golden_angle
    r = np.sqrt(np.maximum(0.0, 1.0 - z * z))
    return np.column_stack((r * np.cos(phi), r * np.sin(phi), z))


def transverse_basis(nvec):
    """Return two orthonormal transverse vectors e1,e2 for every unit n."""
    nvec = np.asarray(nvec, dtype=float)
    idx = np.argmin(np.abs(nvec), axis=1)
    ref = np.zeros_like(nvec)
    ref[np.arange(len(nvec)), idx] = 1.0
    e1 = np.cross(nvec, ref)
    e1 /= np.linalg.norm(e1, axis=1)[:, None]
    e2 = np.cross(nvec, e1)
    e2 /= np.linalg.norm(e2, axis=1)[:, None]
    return e1, e2


def paired_transverse_samples(n_directions):
    """Each wave-vector direction gets both orthogonal transverse polarizations."""
    n = fibonacci_sphere(n_directions)
    e1, e2 = transverse_basis(n)
    nr = np.repeat(n, 2, axis=0)
    w = np.empty_like(nr)
    w[0::2] = e1
    w[1::2] = e2
    return nr, w, n, e1, e2


def rotation_matrix(seed):
    rng = np.random.default_rng(int(seed))
    q, r = np.linalg.qr(rng.normal(size=(3, 3)))
    signs = np.sign(np.diag(r))
    signs[signs == 0.0] = 1.0
    q = q @ np.diag(signs)
    if np.linalg.det(q) < 0.0:
        q[:, 0] *= -1.0
    return q


def shear_matrix(gamma, plane):
    plane = str(plane).lower()
    mapping = {"xy": (0, 1), "yz": (1, 2), "zx": (2, 0)}
    if plane not in mapping:
        raise ValueError(f"unknown shear plane {plane!r}")
    a, b = mapping[plane]
    f = np.eye(3)
    f[a, b] = float(gamma)
    return f
