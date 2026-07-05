"""
Hydrogenic 1s wavefunction and ionization energy for the SST-71 benchmark.
Uses SST Bohr radius a0_sst by default. All in SI (r in m, psi in m^{-3/2}).
"""

from __future__ import annotations

import numpy as np
import constants

# Default Bohr radius: SST canonical scale
_default_a0 = constants.a0_sst
# Ionization energy = ground-state binding (Rydberg scale)
I1 = constants.E_R


def psi_1s(r: float | np.ndarray, a0: float | None = None) -> float | np.ndarray:
    """
    Normalized hydrogenic 1s wavefunction: psi_1s(r) = (pi * a0^3)^{-1/2} * exp(-r/a0).

    Parameters
    ----------
    r : float or ndarray
        Radial distance in m (scalar or array).
    a0 : float, optional
        Bohr radius in m. If None, uses constants.a0_sst.

    Returns
    -------
    float or ndarray
        psi_1s in m^{-3/2}. Same shape as r.

    Notes
    -----
    Convention: int |psi_1s|^2 d^3r = 1 over all space.
    """
    if a0 is None:
        a0 = _default_a0
    if a0 <= 0:
        raise ValueError("a0 must be positive.")
    r = np.asarray(r)
    norm = (np.pi * (a0 ** 3)) ** (-0.5)
    return norm * np.exp(-r / a0)
