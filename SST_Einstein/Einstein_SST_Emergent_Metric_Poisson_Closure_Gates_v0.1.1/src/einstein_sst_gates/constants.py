import math
V_SWIRL = 1.09384563e6
R_C = 1.40897017e-15
RHO_CORE = 3.8934358266918687e18
RHO_F = 7.0e-7
C_LIGHT = 299792458.0
G_NEWTON = 6.67430e-11
GAMMA = 2.0 * math.pi * R_C * V_SWIRL
F_SWIRL_MAX = 29.053507
F_GR_MAX = 3.02563e43
CANONICAL = {
    "v_swirl_m_s": V_SWIRL,
    "r_c_m": R_C,
    "rho_core_kg_m3": RHO_CORE,
    "rho_f_kg_m3": RHO_F,
    "gamma_m2_s": GAMMA,
    "c_m_s": C_LIGHT,
    "G_m3_kg_s2": G_NEWTON,
    "F_swirl_max_N": F_SWIRL_MAX,
    "F_gr_max_N": F_GR_MAX,
}
