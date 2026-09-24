import numpy as np

def wavenumbers(n: int, L: float):
    k = 2.0 * np.pi * np.fft.fftfreq(n, d=L / n)
    return np.meshgrid(k, k, k, indexing="ij")

def derivative_axis(f, axis: int, L: float):
    n = f.shape[axis]
    k = 2.0 * np.pi * np.fft.fftfreq(n, d=L / n)
    shape = [1] * f.ndim
    shape[axis] = n
    K = k.reshape(shape)
    fh = np.fft.fft(f, axis=axis)
    return np.fft.ifft(1j * K * fh, axis=axis).real

def grad_scalar(f, L: float):
    Ks = wavenumbers(f.shape[0], L)
    fh = np.fft.fftn(f)
    return np.stack([np.fft.ifftn(1j * K * fh).real for K in Ks], axis=-1)

def grad_vector(u, L: float):
    # grad[...,i,j] = d_j u_i
    return np.stack([grad_scalar(u[..., i], L) for i in range(3)], axis=-2)

def stress_source(u, L: float):
    # Q = d_i d_j (u_i u_j)
    Ks = wavenumbers(u.shape[0], L)
    out = np.zeros(u.shape[:-1], dtype=float)
    for i in range(3):
        for j in range(3):
            tij = u[..., i] * u[..., j]
            th = np.fft.fftn(tij)
            out += np.fft.ifftn(-(Ks[i] * Ks[j]) * th).real
    return out

def poisson_periodic(source, L: float):
    Ks = wavenumbers(source.shape[0], L)
    k2 = Ks[0] ** 2 + Ks[1] ** 2 + Ks[2] ** 2
    sh = np.fft.fftn(source)
    ph = np.zeros_like(sh)
    mask = k2 > 0
    ph[mask] = -sh[mask] / k2[mask]
    phi = np.fft.ifftn(ph).real
    lap = np.fft.ifftn(-k2 * ph).real
    return phi, lap
