from __future__ import annotations
import math

V_SWIRL = 1.09384563e6               # m s^-1
R_C = 1.40897017e-15                 # m
RHO_CORE = 3.8934358266918687e18     # kg m^-3
RHO_F = 7.0e-7                       # kg m^-3
F_SWIRL_MAX = 29.053507              # N
F_GR_MAX = 3.02563e43                # N
C_LIGHT = 299_792_458.0              # m s^-1
GAMMA_0 = 2.0 * math.pi * R_C * V_SWIRL
OMEGA_CORE = V_SWIRL / R_C
F_CORE = OMEGA_CORE / (2.0 * math.pi)
TAU_CORE = R_C / V_SWIRL

CANONICAL_CONSTANTS = {
    "v_swirl_m_s": V_SWIRL,
    "r_c_m": R_C,
    "rho_core_kg_m3": RHO_CORE,
    "rho_f_kg_m3": RHO_F,
    "F_swirl_max_N": F_SWIRL_MAX,
    "F_gr_max_N": F_GR_MAX,
    "c_m_s": C_LIGHT,
    "Gamma_0_m2_s": GAMMA_0,
    "omega_core_rad_s": OMEGA_CORE,
    "f_core_Hz": F_CORE,
    "tau_core_s": TAU_CORE,
}
