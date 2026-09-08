"""Canonical SST constants used for dimensional reporting only.

The numerical phase gates are formulated dimensionlessly and do not use alpha.
"""
from __future__ import annotations
import math

V_SWIRL = 1.09384563e6                 # m s^-1
R_C = 1.40897017e-15                   # m
RHO_CORE = 3.8934358266918687e18       # kg m^-3
RHO_F = 7.0e-7                          # kg m^-3
F_SWIRL_MAX = 29.053507                 # N
F_GR_MAX = 3.02563e43                   # N
GAMMA_SST = 2.0 * math.pi * R_C * V_SWIRL  # m^2 s^-1
OMEGA0_SST = V_SWIRL / R_C              # s^-1
F0_SST = V_SWIRL / (2.0 * math.pi * R_C) # Hz
