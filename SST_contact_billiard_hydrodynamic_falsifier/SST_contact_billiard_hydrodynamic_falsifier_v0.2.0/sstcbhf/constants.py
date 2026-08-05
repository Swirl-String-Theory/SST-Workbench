from __future__ import annotations

import math

V_SWIRL = 1.09384563e6          # m s^-1
R_C = 1.40897017e-15           # m
RHO_CORE = 3.8934358266918687e18  # kg m^-3
RHO_F = 7.0e-7                 # kg m^-3
F_SWIRL_MAX = 29.053507        # N
F_GR_MAX = 3.02563e43          # N

GAMMA_CANONICAL = 2.0 * math.pi * R_C * V_SWIRL  # m^2 s^-1
T_CORE = R_C / V_SWIRL                            # s

SST_CONSTANTS = {
    "v_swirl_m_s": V_SWIRL,
    "r_c_m": R_C,
    "rho_core_kg_m3": RHO_CORE,
    "rho_f_kg_m3": RHO_F,
    "F_swirl_max_N": F_SWIRL_MAX,
    "F_gr_max_N": F_GR_MAX,
    "Gamma_canonical_m2_s": GAMMA_CANONICAL,
    "t_core_s": T_CORE,
}
