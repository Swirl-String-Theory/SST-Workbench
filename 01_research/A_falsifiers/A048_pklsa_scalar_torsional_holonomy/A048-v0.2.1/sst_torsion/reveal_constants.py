import math
V_SWIRL = 1.09384563e6       # m s^-1
R_C = 1.40897017e-15         # m
RHO_CORE = 3.8934358266918687e18  # kg m^-3
RHO_F = 7.0e-7               # kg m^-3

def derived_scales():
    gamma_c = 2.0 * math.pi * R_C * V_SWIRL
    beta_c = gamma_c / (4.0 * math.pi)
    t_c = R_C / V_SWIRL
    omega_c = V_SWIRL / R_C
    return {
        "v_swirl_m_s": V_SWIRL,
        "r_c_m": R_C,
        "Gamma_c_m2_s": gamma_c,
        "beta_c_m2_s": beta_c,
        "t_c_s": t_c,
        "omega_c_s-1": omega_c,
        "rho_core_kg_m3": RHO_CORE,
        "rho_f_kg_m3": RHO_F,
    }
