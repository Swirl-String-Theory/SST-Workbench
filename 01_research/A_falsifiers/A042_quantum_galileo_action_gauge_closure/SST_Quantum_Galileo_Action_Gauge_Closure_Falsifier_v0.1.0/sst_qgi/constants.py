import math

V_SWIRL = 1.09384563e6
R_C = 1.40897017e-15
RHO_CORE = 3.8934358266918687e18
RHO_F = 7.0e-7

H_SI = 6.62607015e-34
HBAR_SI = H_SI / (2.0 * math.pi)

def h_sst() -> float:
    return 4.0 * math.pi**2 * RHO_CORE * V_SWIRL * R_C**4

def hbar_sst() -> float:
    return h_sst() / (2.0 * math.pi)

def action_scale_audit() -> dict:
    hs = h_sst()
    return {
        "v_swirl_m_s": V_SWIRL,
        "r_c_m": R_C,
        "rho_core_kg_m3": RHO_CORE,
        "rho_f_kg_m3": RHO_F,
        "h_sst_J_s": hs,
        "h_si_J_s": H_SI,
        "h_sst_over_h_minus_1": hs / H_SI - 1.0,
        "phase_prefactor_sst_over_si_minus_1": H_SI / hs - 1.0,
    }
