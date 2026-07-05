"""
Attractive Coulomb continuum radial functions using mpmath.
Conventions: eta_C = -Z/(k*a0), rho = k*r; regular solution F_l(eta, rho).
Used for bound-continuum matrix elements; normalization is internally consistent
so that asymmetry A_tot is independent of overall scale.
"""

from __future__ import annotations

import numpy as np
import mpmath as mp

try:
    from scipy.special import sph_harm as _sph_harm
    def _Y_lm(m: int, l: int, theta: float, phi: float):  # colatitude theta, azimuth phi
        return _sph_harm(m, l, phi, theta)  # scipy legacy: sph_harm(m, l, phi, theta)
except ImportError:
    from scipy.special import sph_harm_y
    def _Y_lm(m: int, l: int, theta: float, phi: float):
        return sph_harm_y(l, m, theta, phi)

import constants

# Default precision for Coulomb evaluations
_DEFAULT_DPS = 50

# Continuum normalization: we use k-normalized radial wave so that
# int_0^infty R_El(r)^2 r^2 dr = 1 (unit flux convention).
# The radial wave u_l(r) = r*R_l(r) satisfies the radial ODE; standard
# regular Coulomb solution F_l(eta, rho) with rho = k*r.
# We take R_El(r) = (2/pi)^(1/2) * (1/r) * F_l(eta, k*r) / (k*r) for r>0
# and document that density of states is absorbed in rate formula.
# For simplicity we use R_El(r) = F_l(eta, k*r) / (k*r) up to a constant
# so that all partial waves use the same convention (asymmetry unchanged).


def set_coulomb_precision(dps: int = _DEFAULT_DPS) -> None:
    """Set mpmath decimal precision for Coulomb functions."""
    if dps < 10:
        raise ValueError("dps must be >= 10 for stability.")
    mp.mp.dps = dps


def coulomb_eta(E_k: float, Z: int = 1, a0: float | None = None) -> float:
    """
    Coulomb parameter eta = -Z/(k*a0) for attractive potential (eta < 0).
    k = sqrt(2*m_e*E_k)/hbar in SI.
    """
    if E_k <= 0:
        raise ValueError("E_k must be positive (continuum).")
    if a0 is None:
        a0 = constants.a0_sst
    k = np.sqrt(2.0 * constants.m_e * E_k) / constants.hbar
    return -float(Z) / (k * a0)


def coulomb_k(E_k: float) -> float:
    """Wave number k = sqrt(2*m_e*E_k)/hbar in 1/m."""
    if E_k <= 0:
        raise ValueError("E_k must be positive.")
    return np.sqrt(2.0 * constants.m_e * E_k) / constants.hbar


def radial_coulomb(E_k: float, l: int, r: float, Z: int = 1, a0: float | None = None) -> float:
    """
    Regular Coulomb radial wave R_El(r) for attractive Z/r potential.
    Uses mpmath coulombf(l, eta, rho) with rho = k*r, eta = -Z/(k*a0).
    Returns float for use in quadrature; R(r) = F_l(eta, k*r) / (k*r) for r>0,
    and 0 at r=0 (limit gives correct behavior).
    Units: R has dimension 1/length^(3/2) so that int R^2 r^2 dr is dimensionless
    with our convention; overall normalization is fixed and consistent.

    Parameters
    ----------
    E_k : float
        Kinetic energy in J.
    l : int
        Angular momentum (>= 0).
    r : float
        Radius in m.
    Z : int
        Nuclear charge (default 1).
    a0 : float, optional
        Bohr radius in m (default a0_sst).

    Returns
    -------
    float
        R_El(r) for continuum state; 0 at r=0.
    """
    if E_k <= 0:
        raise ValueError("E_k must be positive.")
    if l < 0:
        raise ValueError("l must be non-negative.")
    if r < 0:
        raise ValueError("r must be non-negative.")
    if a0 is None:
        a0 = constants.a0_sst

    if r == 0:
        return 0.0

    k = coulomb_k(E_k)
    eta = coulomb_eta(E_k, Z=Z, a0=a0)
    rho = k * r

    # mpmath coulombf(l, eta, rho); F is the regular solution
    F_val = mp.coulombf(l, eta, rho)
    # Radial wave: R(r) = F_l(eta, k*r) / (k*r) (standard convention)
    # Scale by 1/sqrt(k) for k-normalized continuum (optional; cancel in asymmetry)
    R = float(F_val) / (k * r)
    return R


def continuum_wavefunction_spherical(
    r: float, theta: float, phi: float,
    E_k: float, l: int, m: int,
    Z: int = 1, a0: float | None = None,
) -> complex:
    """
    Continuum state psi_Elm(r, theta, phi) = R_El(r) * Y_lm(theta, phi).
    scipy.sph_harm(m, l, phi, theta): theta is colatitude [0, pi], phi is azimuth [0, 2*pi].
    Condon-Shortley phase included in scipy Y_lm.
    """
    if abs(m) > l:
        return 0.0
    R = radial_coulomb(E_k, l, r, Z=Z, a0=a0)
    Y = _Y_lm(m, l, theta, phi)
    return R * Y


def get_continuum_normalization_note() -> str:
    """
    Return a string documenting the continuum normalization convention used.
    Rate formula uses the same normalization for both helicities so A_tot is unchanged.
    """
    return (
        "Coulomb radial wave R_El(r) = F_l(eta, k*r)/(k*r) with F_l from mpmath.coulombf. "
        "Consistent k-normalization; density of states factor same for both h, so A_tot unchanged."
    )


# Ensure default precision on import
set_coulomb_precision(_DEFAULT_DPS)
