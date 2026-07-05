"""
Pure-helicity circulation probe gamma_h and control variants (non-helical, broken axisymmetry,
helical_mode_plus1 one-sided Fourier perturbation).
Spatial part only: gamma_h = A_gamma * f(rho,z) * exp(i*(h*phi + q*z)).
Coordinates: rho = r*sin(theta), z = r*cos(theta).
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np


def envelope(rho: float | np.ndarray, z: float | np.ndarray,
             w_r: float, w_z: float) -> float | np.ndarray:
    """
    Axisymmetric Gaussian envelope f(rho, z) = exp(-rho^2/(2*w_r^2)) * exp(-z^2/(2*w_z^2)).
    """
    return np.exp(-(rho ** 2) / (2.0 * w_r ** 2)) * np.exp(-(z ** 2) / (2.0 * w_z ** 2))


def gamma_h(
    r: float | np.ndarray,
    theta: float | np.ndarray,
    phi: float | np.ndarray,
    h: int,
    q: float,
    w_r: float,
    w_z: float,
    A_gamma: float = 1.0,
    eps: float = 0.0,
) -> np.ndarray | complex:
    """
    Pure-helicity probe (spatial part): gamma_h = A_gamma * f(rho,z) * (1 + eps*cos(2*phi)) * exp(i*(h*phi + q*z)).
    r, theta, phi in spherical: r >= 0, theta in [0, pi], phi in [0, 2*pi].
    eps=0: axisymmetric envelope. eps>0: broken axisymmetry (control).
    h=0: non-helical (no phi in phase for the helical part; phase is i*q*z only).

    Returns
    -------
    complex or ndarray
        Probe field value(s). Same shape as broadcast(r, theta, phi).
    """
    rho = r * np.sin(theta)
    z = r * np.cos(theta)
    f = envelope(rho, z, w_r, w_z)
    # Broken axisymmetry: multiply envelope by (1 + eps*cos(2*phi))
    if eps != 0:
        f = f * (1.0 + eps * np.cos(2.0 * phi))
    phase = h * phi + q * z
    return A_gamma * f * (np.cos(phase) + 1j * np.sin(phase))


def gamma_h_helical(
    r: float | np.ndarray, theta: float | np.ndarray, phi: float | np.ndarray,
    h: int, q: float, w_r: float, w_z: float, A_gamma: float = 1.0,
) -> np.ndarray | complex:
    """Axisymmetric helical probe (eps=0)."""
    return gamma_h(r, theta, phi, h, q, w_r, w_z, A_gamma=A_gamma, eps=0.0)


def gamma_h_non_helical(
    r: float | np.ndarray, theta: float | np.ndarray, phi: float | np.ndarray,
    q: float, w_r: float, w_z: float, A_gamma: float = 1.0,
) -> np.ndarray | complex:
    """Non-helical probe: h=0, so phase = i*q*z only."""
    return gamma_h(r, theta, phi, 0, q, w_r, w_z, A_gamma=A_gamma, eps=0.0)


def gamma_h_broken_axisymmetry(
    r: float | np.ndarray, theta: float | np.ndarray, phi: float | np.ndarray,
    h: int, q: float, w_r: float, w_z: float, eps: float, A_gamma: float = 1.0,
) -> np.ndarray | complex:
    """Broken axisymmetry: envelope * (1 + eps*cos(2*phi)), same phase exp(i*(h*phi + q*z))."""
    return gamma_h(r, theta, phi, h, q, w_r, w_z, A_gamma=A_gamma, eps=eps)


def gamma_axisymmetric_reduced(
    r: float | np.ndarray,
    theta: float | np.ndarray,
    q: float,
    w_r: float,
    w_z: float,
    A_gamma: float = 1.0,
) -> np.ndarray | complex:
    """
    Phi-independent factor for axisymmetric probe used in the 2D (r, theta) integral.
    After the phi integral, the only remaining probe factor is A_gamma * f(rho,z) * exp(i*q*z).
    Used with phi=0; h enters only via the selection rule m=h, not in this value.
    """
    rho = r * np.sin(theta)
    z = r * np.cos(theta)
    f = envelope(rho, z, w_r, w_z)
    return A_gamma * f * (np.cos(q * z) + 1j * np.sin(q * z))


def get_probe_harmonic_components(
    probe_type: str,
    h: int,
    eps: float,
) -> List[Tuple[int, complex]]:
    """
    Return azimuthal harmonic components as a list of (n, coeff), meaning the probe
    contributes coeff * exp(i*n*phi) in the axisymmetric envelope factor.

    - helical: [(h, 1)]
    - non_helical: [(0, 1)]
    - helical_mode_plus1: [(h, 1), (h+1, eps)] so that
      gamma = A_gamma * f * exp(i*q*z) * [exp(i*h*phi) + eps*exp(i*(h+1)*phi)].
      For h=+1: m channels +1 and +2; for h=-1: m channels -1 and 0.
    """
    if probe_type == "non_helical":
        return [(0, 1.0 + 0.0j)]
    if probe_type == "helical":
        return [(h, 1.0 + 0.0j)]
    if probe_type == "helical_mode_plus1":
        return [(h, 1.0 + 0.0j), (h + 1, eps + 0.0j)]
    # Legacy broken-axisymmetry is not a finite harmonic sum; caller uses 3D path
    return []


def gamma_h_helical_mode_plus1(
    r: float | np.ndarray,
    theta: float | np.ndarray,
    phi: float | np.ndarray,
    h: int,
    q: float,
    w_r: float,
    w_z: float,
    eps: float,
    A_gamma: float = 1.0,
) -> np.ndarray | complex:
    """
    One-sided Fourier perturbation: gamma = A_gamma * f(rho,z) * exp(i*q*z) * exp(i*h*phi) * (1 + eps*exp(i*phi)).
    Equivalent to A_gamma * f * exp(i*q*z) * [exp(i*h*phi) + eps*exp(i*(h+1)*phi)].
    Breaks m↔-m pairing: h=+1 -> m=+1,+2; h=-1 -> m=-1,0.
    """
    rho = r * np.sin(theta)
    z = r * np.cos(theta)
    f = envelope(rho, z, w_r, w_z)
    phase_base = h * phi + q * z
    # exp(i*h*phi) + eps*exp(i*(h+1)*phi) = exp(i*h*phi) * (1 + eps*exp(i*phi))
    term1 = np.cos(phase_base) + 1j * np.sin(phase_base)
    phase_plus = (h + 1) * phi + q * z
    term2 = eps * (np.cos(phase_plus) + 1j * np.sin(phase_plus))
    return A_gamma * f * (term1 + term2)
