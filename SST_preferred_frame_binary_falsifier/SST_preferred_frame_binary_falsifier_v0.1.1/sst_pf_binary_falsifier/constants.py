from __future__ import annotations

import math

# User-locked SST constants
V_SWIRL = 1.09384563e6  # m s^-1
R_C = 1.40897017e-15  # m
RHO_CORE = 3.8934358266918687e18  # kg m^-3
RHO_F = 7.0e-7  # kg m^-3
F_SWIRL_MAX = 29.053507  # N
F_GR_MAX = 3.02563e43  # N
C = 299_792_458.0  # m s^-1, exact SI
GAMMA_CANON = 2.0 * math.pi * R_C * V_SWIRL  # m^2 s^-1
V_SWIRL_OVER_C = V_SWIRL / C
V_SWIRL_OVER_C_SQ = V_SWIRL_OVER_C**2

# PSR J1738+0333 values quoted in Vaglio et al. (2026), arXiv:2605.01436
J1738_PDOT_OBS = -1.82e-14  # s s^-1
J1738_PDOT_OBS_SIGMA = 0.25e-14
J1738_PDOT_SHK = 9.3e-15
J1738_PDOT_SHK_SIGMA = 0.6e-15
J1738_PDOT_GAL = -3.0e-16
J1738_PDOT_GAL_SIGMA = 0.3e-16
J1738_ALPHA1_LOWER_68 = -4.4e-5
J1738_ALPHA1_LOWER_90 = -7.2e-5
SOLAR_SYSTEM_ALPHA1_ABS = 1.0e-4  # review-level bound quoted in the paper
SOLAR_SYSTEM_ALPHA2_ABS = 1.0e-7  # review-level bound quoted in the paper
