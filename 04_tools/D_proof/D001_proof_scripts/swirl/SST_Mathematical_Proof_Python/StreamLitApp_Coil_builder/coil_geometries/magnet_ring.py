# magnet_ring.py
from __future__ import annotations

import numpy as np
from typing import Tuple


def generate_magnet_dipole_ring(
        num_magnets: int,
        radius: float,
        toroidal_degrees: float,
        poloidal_degrees: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Genereert een ring van dipoolmagneten met toroidale en poloidale modulatie.

    Args:
        num_magnets: Aantal magneten op de ring.
        radius: Ringradius in meter.
        toroidal_degrees: Totale toroidale twist (in graden) over de ring.
        poloidal_degrees: Pseudo-poloidale tilt amplitude (in graden).

    Returns:
        positions: (N, 3) array met de magnetposities.
        moments:   (N, 3) array met genormaliseerde dipoolmoment-richtingen.
    """
    positions = []
    orientations = []

    for i in range(num_magnets):
        phi = 2.0 * np.pi * i / num_magnets

        # Positie op de ring (z=0)
        x = radius * np.cos(phi)
        y = radius * np.sin(phi)
        z = 0.0
        positions.append([x, y, z])

        # Toroidale twist langs index
        toroidal_angle = np.deg2rad(toroidal_degrees) * i / num_magnets

        # Pseudo-poloidale tilt via sin(phi)
        poloidal_angle = np.deg2rad(poloidal_degrees) * np.sin(phi)

        # Richting van het dipoolmoment
        mx = np.cos(2.0 * phi + toroidal_angle)
        my = np.sin(2.0 * phi + toroidal_angle)
        mz = np.sin(poloidal_angle)

        m = np.array([mx, my, mz], dtype=float)
        m /= np.linalg.norm(m)
        orientations.append(m)

    return np.asarray(positions), np.asarray(orientations)