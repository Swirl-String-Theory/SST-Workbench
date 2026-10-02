import math
import numpy as np
from .backend import cross_product


class EulerSpectral3D:
    """Dealiased Fourier pseudospectral incompressible Euler + tangent-linear solver."""

    def __init__(self, n=12, length=2.0 * math.pi):
        self.n = int(n)
        self.length = float(length)
        dx = self.length / self.n
        kval = 2.0 * math.pi * np.fft.fftfreq(self.n, d=dx)
        self.kx, self.ky, self.kz = np.meshgrid(kval, kval, kval, indexing="ij")
        self.kvec = np.stack([self.kx, self.ky, self.kz], axis=-1)
        self.k2 = self.kx**2 + self.ky**2 + self.kz**2
        self.nonzero = self.k2 > 0.0

        # 2/3 de-aliasing using integer Fourier indices.
        modes = np.fft.fftfreq(self.n) * self.n
        mx, my, mz = np.meshgrid(modes, modes, modes, indexing="ij")
        cutoff = self.n // 3
        self.dealias = (
            (np.abs(mx) <= cutoff)
            & (np.abs(my) <= cutoff)
            & (np.abs(mz) <= cutoff)
        )

    def fft(self, u):
        return np.fft.fftn(u, axes=(-4, -3, -2))

    def ifft_real(self, uhat):
        return np.fft.ifftn(uhat, axes=(-4, -3, -2)).real

    def project(self, uhat):
        arr = np.asarray(uhat, dtype=np.complex128)
        dot = np.sum(arr * self.kvec, axis=-1)
        safe_k2 = np.where(self.nonzero, self.k2, 1.0)
        factor = np.where(self.nonzero, dot / safe_k2, 0.0)
        out = arr - factor[..., None] * self.kvec
        out[..., 0, 0, 0, :] = 0.0
        return out

    def filter(self, uhat):
        out = np.asarray(uhat, dtype=np.complex128) * self.dealias[..., None]
        return self.project(out)

    def curl_hat(self, uhat):
        return 1j * np.cross(self.kvec, uhat)

    def base_rhs(self, uhat):
        uhat = self.filter(uhat)
        u = self.ifft_real(uhat)
        omega = self.ifft_real(self.curl_hat(uhat))
        rot = cross_product(u, omega)
        return self.filter(self.fft(rot))

    def tangent_rhs(self, uhat, dhat):
        uhat = self.filter(uhat)
        dhat = self.filter(dhat)
        u = self.ifft_real(uhat)
        omega = self.ifft_real(self.curl_hat(uhat))
        d = self.ifft_real(dhat)
        domega = self.ifft_real(self.curl_hat(dhat))
        # Linearization of P[u x omega]: P[d x omega + u x domega].
        omega_b = omega[None, ...] if d.ndim == 5 else omega
        u_b = u[None, ...] if d.ndim == 5 else u
        rhs_phys = cross_product(d, omega_b) + cross_product(u_b, domega)
        return self.filter(self.fft(rhs_phys))

    def coupled_rhs(self, uhat, dhat):
        return self.base_rhs(uhat), self.tangent_rhs(uhat, dhat)

    def rk4_step(self, uhat, dhat, dt):
        k1u, k1d = self.coupled_rhs(uhat, dhat)
        k2u, k2d = self.coupled_rhs(uhat + 0.5*dt*k1u, dhat + 0.5*dt*k1d)
        k3u, k3d = self.coupled_rhs(uhat + 0.5*dt*k2u, dhat + 0.5*dt*k2d)
        k4u, k4d = self.coupled_rhs(uhat + dt*k3u, dhat + dt*k3d)
        un = uhat + (dt/6.0)*(k1u + 2.0*k2u + 2.0*k3u + k4u)
        dn = dhat + (dt/6.0)*(k1d + 2.0*k2d + 2.0*k3d + k4d)
        return self.filter(un), self.filter(dn)

    def rk4_base_step(self, uhat, dt):
        """Fourth-order step for the base Euler state only."""
        k1 = self.base_rhs(uhat)
        k2 = self.base_rhs(uhat + 0.5 * dt * k1)
        k3 = self.base_rhs(uhat + 0.5 * dt * k2)
        k4 = self.base_rhs(uhat + dt * k3)
        return self.filter(uhat + (dt / 6.0) * (k1 + 2.0*k2 + 2.0*k3 + k4))

    def rk4_tangent_frozen_step(self, uhat, dhat, dt):
        """Tangent-linear RK4 step with the base state held fixed."""
        k1 = self.tangent_rhs(uhat, dhat)
        k2 = self.tangent_rhs(uhat, dhat + 0.5 * dt * k1)
        k3 = self.tangent_rhs(uhat, dhat + 0.5 * dt * k2)
        k4 = self.tangent_rhs(uhat, dhat + dt * k3)
        return self.filter(dhat + (dt / 6.0) * (k1 + 2.0*k2 + 2.0*k3 + k4))

    def relative_equilibrium_translation_fit(self, uhat):
        """Fit a uniform translation U to du/dt = -U.grad(u).

        Returns (U, residual, rhs_rate), where residual is the relative L2
        error after subtracting the best translational group tangent. A true
        travelling relative equilibrium would have residual near zero.
        """
        uhat = self.filter(uhat)
        rhs = self.base_rhs(uhat)
        basis = [
            -1j * self.kx[..., None] * uhat,
            -1j * self.ky[..., None] * uhat,
            -1j * self.kz[..., None] * uhat,
        ]
        A = np.stack([b.ravel() for b in basis], axis=1)
        b = rhs.ravel()
        Ar = np.concatenate([A.real, A.imag], axis=0)
        br = np.concatenate([b.real, b.imag], axis=0)
        U, *_ = np.linalg.lstsq(Ar, br, rcond=None)
        pred = sum(float(U[j]) * basis[j] for j in range(3))
        residual = float(np.linalg.norm((rhs - pred).ravel()) / max(np.linalg.norm(rhs.ravel()), 1e-300))
        rhs_rate = float(np.linalg.norm(rhs.ravel()) / max(np.linalg.norm(uhat.ravel()), 1e-300))
        return np.asarray(U, dtype=float), residual, rhs_rate

    def translate_state(self, uhat, velocity, time):
        """Exact Fourier translation for u(x,t)=u0(x-U t)."""
        U = np.asarray(velocity, dtype=float)
        phase = np.exp(-1j * (self.kx*U[0] + self.ky*U[1] + self.kz*U[2]) * float(time))
        return self.filter(uhat * phase[..., None])

    def energy(self, uhat):
        u = self.ifft_real(uhat)
        return 0.5 * float(np.mean(np.sum(u*u, axis=-1)))

    def urms(self, uhat):
        return math.sqrt(2.0 * self.energy(uhat))

    def divergence_fourier_rel(self, uhat):
        dot = np.sum(uhat * self.kvec, axis=-1)
        num = float(np.linalg.norm(dot.ravel()))
        den = float(np.linalg.norm((uhat * np.sqrt(self.k2)[..., None]).ravel()))
        return num / max(den, 1e-300)


def random_isotropic_background(grid, seed, shell_min=3.0, shell_max=4.2, urms=1.0):
    rng = np.random.default_rng(int(seed))
    x = rng.normal(size=(grid.n, grid.n, grid.n, 3))
    h = grid.project(grid.fft(x))
    kmag = np.sqrt(grid.k2)
    shell = (kmag >= float(shell_min)) & (kmag <= float(shell_max)) & grid.dealias
    h *= shell[..., None]
    h = grid.filter(h)
    current = grid.urms(h)
    if current == 0.0:
        raise RuntimeError("background shell produced zero velocity")
    return h * (float(urms) / current)


def velocity_covariance_isotropy(grid, uhat):
    u = grid.ifft_real(uhat)
    flat = u.reshape((-1, 3))
    cov = (flat.T @ flat) / float(len(flat))
    tr = float(np.trace(cov))
    return cov / tr, float(np.linalg.norm(cov / tr - np.eye(3)/3.0))


def _probe_basis(axis):
    axis = str(axis).lower()
    if axis == "x":
        khat = np.array([1.0, 0.0, 0.0]); e1 = np.array([0.0, 1.0, 0.0]); e2 = np.array([0.0, 0.0, 1.0])
    elif axis == "y":
        khat = np.array([0.0, 1.0, 0.0]); e1 = np.array([0.0, 0.0, 1.0]); e2 = np.array([1.0, 0.0, 0.0])
    elif axis == "z":
        khat = np.array([0.0, 0.0, 1.0]); e1 = np.array([1.0, 0.0, 0.0]); e2 = np.array([0.0, 1.0, 0.0])
    else:
        raise ValueError("axis must be x, y, or z")
    return khat, e1, e2


def helical_probe_field(grid, axis, mode, helicity, amplitude=1.0):
    khat, e1, e2 = _probe_basis(axis)
    h = 1 if int(helicity) >= 0 else -1
    coord = np.arange(grid.n, dtype=float) * grid.length / grid.n
    X, Y, Z = np.meshgrid(coord, coord, coord, indexing="ij")
    phase = (2.0*math.pi/grid.length) * int(mode) * (khat[0]*X + khat[1]*Y + khat[2]*Z)
    field = float(amplitude) * (
        np.cos(phase)[..., None] * e1 + h * np.sin(phase)[..., None] * e2
    )
    return grid.filter(grid.fft(field))


def probe_descriptor(grid, axis, mode, helicity):
    khat, e1, e2 = _probe_basis(axis)
    h = 1 if int(helicity) >= 0 else -1
    mode = int(mode)
    idx = [0, 0, 0]
    ax = {"x": 0, "y": 1, "z": 2}[axis]
    idx[ax] = mode % grid.n
    # FFT coefficient at +k is proportional to e1 - i*h*e2.
    pol = (e1 - 1j*h*e2) / math.sqrt(2.0)
    kphys = (2.0*math.pi/grid.length) * mode
    return {"axis": axis, "mode": mode, "helicity": h, "index": tuple(idx), "polarization": pol, "k": kphys}


def probe_amplitude(dhat, desc, probe_index=None):
    arr = dhat if probe_index is None else dhat[probe_index]
    coeff = arr[desc["index"]]
    return complex(np.vdot(desc["polarization"], coeff))


def fit_complex_mode(times, amplitudes, min_relative_amplitude=0.15):
    t = np.asarray(times, dtype=float)
    a = np.asarray(amplitudes, dtype=np.complex128)
    if len(t) < 4:
        raise ValueError("need >=4 time samples")
    mag = np.abs(a)
    mag0 = max(mag[0], 1e-300)
    rel = mag / mag0
    valid = rel >= float(min_relative_amplitude)
    # Need a contiguous leading window to avoid fitting phase after coherence is lost.
    if not valid[0]:
        valid[0] = True
    end = len(t)
    bad = np.where(~valid)[0]
    if len(bad):
        end = max(3, int(bad[0]))
    tt = t[:end]
    aa = a[:end]
    rr = np.maximum(np.abs(aa) / mag0, 1e-300)
    phase = np.unwrap(np.angle(aa / a[0]))
    X = np.column_stack([tt, np.ones_like(tt)])
    slope, intercept = np.linalg.lstsq(X, phase, rcond=None)[0]
    pred = slope*tt + intercept
    ss_res = float(np.sum((phase-pred)**2))
    ss_tot = float(np.sum((phase-np.mean(phase))**2))
    r2 = 1.0 if ss_tot < 1e-30 and ss_res < 1e-30 else (1.0 - ss_res/max(ss_tot,1e-300))
    logmag = np.log(rr)
    damp, _ = np.linalg.lstsq(X, logmag, rcond=None)[0]
    return {
        "omega_signed": float(-slope),
        "omega_abs": float(abs(slope)),
        "phase_fit_r2": float(r2),
        "amplitude_end_relative": float(rel[-1]),
        "amplitude_min_relative": float(np.min(rel)),
        "coherent_fit_fraction": float(end/len(t)),
        "log_amplitude_rate": float(damp),
    }
