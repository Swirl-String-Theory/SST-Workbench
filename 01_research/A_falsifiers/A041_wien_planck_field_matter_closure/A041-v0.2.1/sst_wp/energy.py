from __future__ import annotations
import math
from .kernels import energy_sum

def dimensionless_line_energy(points, offsets, core_fraction, require_native=False):
    """
    Dimensionless regularized line-filament energy.

    Normalization:
        L = 1, Gamma = 1,
        E_hat = (1 / 8 pi) * S_hat

    where S_hat is the double line integral returned by energy_sum().
    No canonical SST constant or SI scale is used.
    """
    s_hat = energy_sum(points, offsets, core_fraction, require_native)
    e_hat = s_hat / (8.0 * math.pi)
    return float(e_hat), float(s_hat)
