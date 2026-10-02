"""Axisymmetric incompressible Euler (+ small nu) with swirl, (r,z) plane.

Fields:
    sigma = r * u_phi          (angular momentum / 'swirl'; materially conserved, nu=0)
    eta   = omega_phi / r      (azimuthal vorticity over r)
Evolution:
    D sigma / Dt = nu * (sigma_rr - sigma_r/r + sigma_zz)
    D eta   / Dt = (1/r^4) d(sigma^2)/dz + nu * (eta_rr + 3 eta_r / r + eta_zz)
Streamfunction (Stokes):  psi_rr - psi_r/r + psi_zz = -r^2 * eta,   u_r = -psi_z/r,  u_z = psi_r/r
Poisson solve: DST-I in z (Dirichlet), vectorized Thomas in r per z-mode.

This is a GRID-level solver: no filament asymptotics anywhere, so it is an
independent test of the Saffman/Moore-Saffman core-constant prediction.
Geometry note: for a vortex RING the filament axis is the phi direction, so
"axial flow along the core" == u_phi, and nonzero u_phi makes the vortex lines
helices around the torus == core twist.
"""
import numpy as np
from scipy.fft import dst, idst


class AxisymSolver:
    def __init__(self, Nr=256, Nz=512, Rmax=3.5, Zmax=7.0, nu=5e-5):
        self.Nr, self.Nz = Nr, Nz
        self.Rmax, self.Zmax = Rmax, Zmax
        self.nu = nu
        self.dr = Rmax / Nr
        self.dz = Zmax / Nz
        self.r = np.arange(Nr + 1) * self.dr          # nodes j=0..Nr, r0=0
        self.z = np.arange(Nz + 1) * self.dz          # nodes i=0..Nz
        self.R2, _ = np.meshgrid(self.r, self.z, indexing="ij")  # (Nr+1, Nz+1)
        self.rcol = self.r[:, None]
        self._build_poisson()
        self.eta = np.zeros((Nr + 1, Nz + 1))
        self.sigma = np.zeros((Nr + 1, Nz + 1))

    # ---------------- Poisson: psi_rr - psi_r/r + psi_zz = -r^2 eta ----------
    def _build_poisson(self):
        Nr, Nz, dr, dz = self.Nr, self.Nz, self.dr, self.dz
        m = np.arange(1, Nz)                                    # z modes
        lam = (2.0 - 2.0 * np.cos(np.pi * m / Nz)) / dz**2      # DST-I eigenvalues
        rj = self.r[1:Nr]                                       # interior radii, j=1..Nr-1
        self.A = (1.0 / dr**2 + 1.0 / (2.0 * rj * dr))[:, None] # sub-diagonal coeff (psi_{j-1})
        self.C = (1.0 / dr**2 - 1.0 / (2.0 * rj * dr))[:, None] # super-diagonal (psi_{j+1})
        B = (-2.0 / dr**2) - lam                                # diagonal per mode (r-independent), (Nz-1,)
        # Thomas forward-elimination tables (RHS-independent)
        n = Nr - 1
        self.cp = np.zeros((n, Nz - 1))
        self.den = np.zeros((n, Nz - 1))
        den = B.copy()
        self.den[0] = den
        self.cp[0] = self.C[0] / den
        for j in range(1, n):
            den = B - self.A[j] * self.cp[j - 1]
            self.den[j] = den
            if j < n - 1:
                self.cp[j] = self.C[j] / den

    def solve_psi(self, eta):
        Nr, Nz = self.Nr, self.Nz
        rhs = -(self.rcol**2) * eta                    # (Nr+1, Nz+1)
        rhs_hat = dst(rhs[1:Nr, 1:Nz], type=1, axis=1, norm="ortho")
        n = Nr - 1
        y = np.empty_like(rhs_hat)
        y[0] = rhs_hat[0] / self.den[0]
        for j in range(1, n):
            y[j] = (rhs_hat[j] - self.A[j] * y[j - 1]) / self.den[j]
        x = np.empty_like(y)
        x[n - 1] = y[n - 1]
        for j in range(n - 2, -1, -1):
            x[j] = y[j] - self.cp[j] * x[j + 1]
        psi = np.zeros((Nr + 1, Nz + 1))
        psi[1:Nr, 1:Nz] = idst(x, type=1, axis=1, norm="ortho")
        return psi

    def velocities(self, psi):
        dr, dz = self.dr, self.dz
        psi_r = np.gradient(psi, dr, axis=0)
        psi_z = np.gradient(psi, dz, axis=1)
        u_r = np.zeros_like(psi)
        u_z = np.zeros_like(psi)
        u_r[1:] = -psi_z[1:] / self.rcol[1:]
        u_z[1:] = psi_r[1:] / self.rcol[1:]
        u_z[0] = 2.0 * psi[1] / self.r[1] ** 2          # axis: psi ~ (1/2) u_z r^2
        u_r[0] = 0.0
        return u_r, u_z

    # ---------------- RHS ----------------------------------------------------
    def rhs(self, eta, sigma):
        dr, dz, nu = self.dr, self.dz, self.nu
        psi = self.solve_psi(eta)
        u_r, u_z = self.velocities(psi)

        def ddr(F):
            return np.gradient(F, dr, axis=0)

        def ddz(F):
            return np.gradient(F, dz, axis=1)

        adv_eta = -(u_r * ddr(eta) + u_z * ddz(eta))
        adv_sig = -(u_r * ddr(sigma) + u_z * ddz(sigma))

        src = np.zeros_like(eta)
        src[1:] = ddz(sigma**2)[1:] / self.rcol[1:] ** 4

        # diffusion
        eta_r, eta_z = ddr(eta), ddz(eta)
        sig_r, sig_z = ddr(sigma), ddz(sigma)
        lap_eta = np.gradient(eta_r, dr, axis=0) + np.gradient(eta_z, dz, axis=1)
        lap_sig = np.gradient(sig_r, dr, axis=0) + np.gradient(sig_z, dz, axis=1)
        diff_eta = nu * lap_eta
        diff_sig = nu * lap_sig
        diff_eta[1:] += nu * 3.0 * eta_r[1:] / self.rcol[1:]
        diff_sig[1:] -= nu * sig_r[1:] / self.rcol[1:]

        d_eta = adv_eta + src + diff_eta
        d_sig = adv_sig + diff_sig
        # boundaries: hold zero at outer walls; axis handled by symmetry (fields ~ 0 there)
        for F in (d_eta, d_sig):
            F[0, :] = 0.0
            F[-1, :] = 0.0
            F[:, 0] = 0.0
            F[:, -1] = 0.0
        return d_eta, d_sig, u_r, u_z

    def step(self, dt):
        """SSP-RK3."""
        e0, s0 = self.eta, self.sigma
        de, ds, u_r, u_z = self.rhs(e0, s0)
        e1, s1 = e0 + dt * de, s0 + dt * ds
        de, ds, _, _ = self.rhs(e1, s1)
        e2 = 0.75 * e0 + 0.25 * (e1 + dt * de)
        s2 = 0.75 * s0 + 0.25 * (s1 + dt * ds)
        de, ds, _, _ = self.rhs(e2, s2)
        self.eta = e0 / 3.0 + 2.0 / 3.0 * (e2 + dt * de)
        self.sigma = s0 / 3.0 + 2.0 / 3.0 * (s2 + dt * ds)
        return float(np.max(np.abs(u_r)) + np.max(np.abs(u_z)))

    # ---------------- diagnostics -------------------------------------------
    def omega_phi(self):
        return self.eta * self.R2

    def circulation(self):
        return float(np.sum(self.omega_phi()) * self.dr * self.dz)

    def impulse(self):
        return float(np.pi * np.sum(self.omega_phi() * self.R2**2) * self.dr * self.dz)

    def centroid(self):
        w = self.omega_phi() * self.R2**2                # impulse-weighted
        tot = np.sum(w)
        Z = np.sum(w * self.z[None, :]) / tot
        R = np.sum(w * self.R2) / tot
        return float(R), float(Z)

    def swirl_energy_integral(self, Zc, halfwidth):
        """J = int u_phi^2 dr dz restricted to |z - Zc| < halfwidth (excludes shed wake)."""
        u_phi = np.zeros_like(self.sigma)
        u_phi[1:] = self.sigma[1:] / self.rcol[1:]
        mask = np.abs(self.z[None, :] - Zc) < halfwidth
        return float(np.sum(u_phi**2 * mask) * self.dr * self.dz)

    def helicity(self):
        psi = self.solve_psi(self.eta)
        u_r, u_z = self.velocities(psi)
        u_phi = np.zeros_like(self.sigma)
        u_phi[1:] = self.sigma[1:] / self.rcol[1:]
        om_r = -np.gradient(u_phi, self.dz, axis=1)
        om_z = np.zeros_like(u_phi)
        om_z[1:] = np.gradient(self.sigma, self.dr, axis=0)[1:] / self.rcol[1:]
        integrand = (u_r * om_r + u_phi * self.omega_phi() + u_z * om_z) * self.R2
        return float(2.0 * np.pi * np.sum(integrand) * self.dr * self.dz)


def init_twisted_ring(sol, Gamma=1.0, R0=1.0, z0=1.5, a=0.18, q=0.0, edge=0.03):
    """Rankine-like ring (tanh-smoothed top hat) + uniform-twist axial core flow.

    w(s) = (q Gamma / 2 pi)(1 - s^2/a^2) on the core cross-section (model A),
    sigma = r * w.  Circulation is normalized numerically to Gamma.
    """
    s = np.sqrt((sol.R2 - R0) ** 2 + (sol.z[None, :] - z0) ** 2)
    prof = 0.5 * (1.0 - np.tanh((s - a) / edge))
    om = prof.copy()
    om *= Gamma / (np.sum(om) * sol.dr * sol.dz)       # normalize circulation
    sol.eta = np.zeros_like(om)
    sol.eta[1:] = om[1:] / sol.rcol[1:]
    w = (q * Gamma / (2.0 * np.pi)) * np.maximum(1.0 - s**2 / a**2, 0.0) * prof
    sol.sigma = sol.R2 * w
    return om, w
