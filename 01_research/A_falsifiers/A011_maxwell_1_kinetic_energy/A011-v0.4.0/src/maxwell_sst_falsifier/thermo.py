from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .constants import EV_J, K_B_J_PER_K


@dataclass(frozen=True)
class Level:
    gap_eV: float
    degeneracy: int = 1


def discrete_partition(levels: Iterable[Level], temperature_K: float) -> dict[str, float]:
    """Return Z, U_eV, Cv_J_per_K, Cv_over_kB for a discrete internal spectrum.

    Ground state is included automatically with energy 0 and degeneracy 1.
    """
    if temperature_K <= 0:
        raise ValueError("temperature_K must be > 0")
    beta_eV = EV_J / (K_B_J_PER_K * temperature_K)
    energies = [0.0]
    degeneracies = [1]
    for level in levels:
        if level.gap_eV < 0:
            raise ValueError("gaps must be non-negative")
        energies.append(float(level.gap_eV))
        degeneracies.append(int(level.degeneracy))
    e = np.asarray(energies, dtype=float)
    g = np.asarray(degeneracies, dtype=float)
    x = -beta_eV * e
    x -= np.max(x)
    w = g * np.exp(x)
    z_scaled = float(np.sum(w))
    p = w / z_scaled
    mean_e = float(np.sum(p * e))
    mean_e2 = float(np.sum(p * e * e))
    var_e = max(0.0, mean_e2 - mean_e**2)
    cv_over_kb = (beta_eV**2) * var_e
    cv = K_B_J_PER_K * cv_over_kb
    # reconstruct Z without overflow for practical gaps
    z = float(np.sum(g * np.exp(-beta_eV * e)))
    return {"Z": z, "U_eV": mean_e, "Cv_J_per_K": cv, "Cv_over_kB": cv_over_kb}


def low_temperature_single_level_asymptotic(gap_eV: float, degeneracy: int, temperature_K: float) -> float:
    """Asymptotic Cv/kB ~ g x^2 exp(-x), x=Delta/kBT."""
    x = gap_eV * EV_J / (K_B_J_PER_K * temperature_K)
    return degeneracy * x * x * math.exp(-x)
