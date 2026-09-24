import numpy as np


def absolute_vorticity(omega_rel, omega_planet):
    """Absolute vorticity vector eta = omega_rel + 2 Omega_p."""
    return np.asarray(omega_rel, dtype=float) + 2.0 * np.asarray(omega_planet, dtype=float)


def coriolis_parameter(omega_planet_magnitude, latitude_rad):
    return 2.0 * float(omega_planet_magnitude) * np.sin(float(latitude_rad))


def vertical_absolute_vorticity(zeta, omega_planet_magnitude, latitude_rad):
    return float(zeta) + coriolis_parameter(omega_planet_magnitude, latitude_rad)


def matched_cyclonic_hemisphere_pair(zeta=1.10, omega_planet=0.35):
    """
    Local tangent-plane north/south pole control.

    A matched cyclonic state has relative vertical vorticity with the same sign
    as the local vertical projection of planetary rotation. Thus both the
    relative and planetary axial vectors reverse under the north/south mapping.
    """
    north_omega_p = np.array([0.0, 0.0, +float(omega_planet)])
    south_omega_p = np.array([0.0, 0.0, -float(omega_planet)])
    north_rel = np.array([0.0, 0.0, +float(zeta)])
    south_rel = np.array([0.0, 0.0, -float(zeta)])
    north_abs = absolute_vorticity(north_rel, north_omega_p)
    south_abs = absolute_vorticity(south_rel, south_omega_p)
    return {
        "north_omega_planet": north_omega_p,
        "south_omega_planet": south_omega_p,
        "north_relative": north_rel,
        "south_relative": south_rel,
        "north_absolute": north_abs,
        "south_absolute": south_abs,
    }


def rossby_number(speed, length, coriolis_f):
    den = abs(float(coriolis_f)) * float(length)
    if den == 0.0:
        return np.inf
    return float(speed) / den
