from __future__ import annotations

import math

C = 299_792_458.0
V_SWIRL = 1.09384563e6
R_C = 1.40897017e-15
BETA_0 = V_SWIRL / C
GAMMA_0 = 2.0 * math.pi * R_C * V_SWIRL
FORMAL_X_HORIZON = BETA_0
FORMAL_X_STAR = math.sqrt(2.0) * BETA_0
ROSENHEAD_HORIZON_THRESHOLD = 0.5 * BETA_0
ROSENHEAD_CRITICAL_THRESHOLD = math.sqrt(8.0 / 27.0) * BETA_0


def as_dict() -> dict[str, float]:
    return {
        "c_m_s": C,
        "v_swirl_m_s": V_SWIRL,
        "r_c_m": R_C,
        "beta_0": BETA_0,
        "Gamma_0_m2_s": GAMMA_0,
        "formal_x_horizon": FORMAL_X_HORIZON,
        "formal_x_star": FORMAL_X_STAR,
        "formal_r_horizon_m": FORMAL_X_HORIZON * R_C,
        "formal_r_star_m": FORMAL_X_STAR * R_C,
        "rosenhead_horizon_threshold_epsilon_over_rc": ROSENHEAD_HORIZON_THRESHOLD,
        "rosenhead_critical_threshold_epsilon_over_rc": ROSENHEAD_CRITICAL_THRESHOLD,
        "rosenhead_horizon_threshold_m": ROSENHEAD_HORIZON_THRESHOLD * R_C,
        "rosenhead_critical_threshold_m": ROSENHEAD_CRITICAL_THRESHOLD * R_C,
    }
