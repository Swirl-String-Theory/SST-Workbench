#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
routeD_maximum_tension_trial.py
===============================

Route D trial scan for SST Planck-time derivation:
maximum gravitational tension F_gr^max from SST-only constants.

Epistemic status:
  [RESEARCH-TRACK / TRIAL]
  This script does NOT prove the maximum-force principle from SST.
  It searches compact dimensionally valid SST-only ansätze for
  F_gr^max ~ c^4/(4G), using no G, L_p, or t_p in candidate formulas.

Main candidate:
  F_D^(1) =
      (16/pi^2) F_swirl^max (rho_core/rho_f) (c/v_swirl)^7

Equivalent density form:
  F_D^(1) =
      (16/pi) rho_core v_swirl^2 r_c^2
      (rho_core/rho_f) (c/v_swirl)^7

because rho_core v_swirl^2 r_c^2 = F_swirl^max/pi
for the canonical horn-density closure.
"""

from __future__ import annotations

import math
import json
import csv
from dataclasses import dataclass, asdict
from pathlib import Path

# Canon / CODATA constants
C = 299_792_458.0
HBAR = 1.054571817e-34
G_REF = 6.67430e-11

VSWIRL = 1.09384563e6
R_C = 1.40897017e-15
RHO_CORE = 3.8934358266918687e18
RHO_F = 7.0e-7
M_E = 9.1093837015e-31
F_SWIRL_MAX = 29.053507

F_GR_REF = C**4/(4.0*G_REF)
T_P_REF = math.sqrt(HBAR*G_REF/C**5)
L_P_REF = C*T_P_REF

@dataclass
class Candidate:
    name: str
    expression: str
    F_N: float
    F_ref_N: float
    ratio: float
    rel_error: float
    t_p_s: float
    t_p_ref_s: float
    t_p_ratio: float
    uses_G_Lp_tp: bool
    status: str

def tp_from_force(F: float) -> float:
    return math.sqrt(HBAR/(4.0*F*C))

def main_candidate() -> Candidate:
    rho_ratio = RHO_CORE/RHO_F
    speed_ratio = C/VSWIRL
    F = (16.0/math.pi**2) * F_SWIRL_MAX * rho_ratio * speed_ratio**7
    return Candidate(
        name="D1_maximum_tension_from_core_impedance",
        expression="(16/pi^2) * F_swirl_max * (rho_core/rho_f) * (c/v_swirl)^7",
        F_N=F,
        F_ref_N=F_GR_REF,
        ratio=F/F_GR_REF,
        rel_error=F/F_GR_REF - 1.0,
        t_p_s=tp_from_force(F),
        t_p_ref_s=T_P_REF,
        t_p_ratio=tp_from_force(F)/T_P_REF,
        uses_G_Lp_tp=False,
        status="RESEARCH_TRACK_CANDIDATE__NOT_DERIVED"
    )

def density_equivalent_candidate() -> Candidate:
    rho_ratio = RHO_CORE/RHO_F
    speed_ratio = C/VSWIRL
    F = (16.0/math.pi) * RHO_CORE * VSWIRL**2 * R_C**2 * rho_ratio * speed_ratio**7
    return Candidate(
        name="D1_density_equivalent",
        expression="(16/pi) * rho_core*v_swirl^2*r_c^2 * (rho_core/rho_f) * (c/v_swirl)^7",
        F_N=F,
        F_ref_N=F_GR_REF,
        ratio=F/F_GR_REF,
        rel_error=F/F_GR_REF - 1.0,
        t_p_s=tp_from_force(F),
        t_p_ref_s=T_P_REF,
        t_p_ratio=tp_from_force(F)/T_P_REF,
        uses_G_Lp_tp=False,
        status="ALGEBRAICALLY_EQUIVALENT_TO_D1_USING_HORN_DENSITY"
    )

def scan_top25():
    """Search compact ansatz families around natural SST force scales."""
    bases = {
        "F_swirl=m_e c^2/(2 r_c)": F_SWIRL_MAX,
        "m_e c^2/r_c": M_E*C**2/R_C,
        "m_e v^2/r_c": M_E*VSWIRL**2/R_C,
        "rho_f v^2 r_c^2": RHO_F*VSWIRL**2*R_C**2,
        "rho_core v^2 r_c^2": RHO_CORE*VSWIRL**2*R_C**2,
        "rho_core c^2 r_c^2": RHO_CORE*C**2*R_C**2,
    }
    rho_ratio = RHO_CORE/RHO_F
    speed_ratio = C/VSWIRL

    rows = []
    for base_name, base_val in bases.items():
        for density_exp in range(-1, 3):
            for speed_exp in range(-10, 12):
                for p in range(-8, 9):
                    for q in range(-6, 7):
                        coeff = (2.0**p) * (math.pi**q)
                        F = base_val * (rho_ratio**density_exp) * (speed_ratio**speed_exp) * coeff
                        if not math.isfinite(F) or F <= 0:
                            continue
                        ratio = F/F_GR_REF
                        rows.append({
                            "formula_family": (
                                f"2^{p} pi^{q} * {base_name} * "
                                f"(rho_core/rho_f)^{density_exp} * (c/v)^{{{speed_exp}}}"
                            ),
                            "base": base_name,
                            "density_exp": density_exp,
                            "speed_exp_c_over_v": speed_exp,
                            "coeff_power_2": p,
                            "coeff_power_pi": q,
                            "coeff_value": coeff,
                            "F_candidate_N": F,
                            "F_target_N": F_GR_REF,
                            "ratio": ratio,
                            "rel_error": ratio - 1.0,
                            "abs_rel_error": abs(ratio - 1.0),
                            "tp_from_candidate_s": tp_from_force(F),
                            "tp_ref_s": T_P_REF,
                            "tp_ratio": tp_from_force(F)/T_P_REF,
                        })
    rows.sort(key=lambda r: r["abs_rel_error"])
    return rows[:25]

def write_outputs(prefix: str = "/mnt/data/routeD_maximum_tension_trial"):
    main = main_candidate()
    dens = density_equivalent_candidate()
    top25 = scan_top25()

    payload = {
        "constants": {
            "c_m_s": C,
            "hbar_J_s": HBAR,
            "G_ref_m3_kg_s2": G_REF,
            "v_swirl_m_s": VSWIRL,
            "r_c_m": R_C,
            "rho_core_kg_m3": RHO_CORE,
            "rho_f_kg_m3": RHO_F,
            "m_e_kg": M_E,
            "F_swirl_max_N": F_SWIRL_MAX,
            "F_gr_ref_N": F_GR_REF,
            "t_p_ref_s": T_P_REF,
            "L_p_ref_m": L_P_REF,
        },
        "candidate_main": asdict(main),
        "candidate_density_equivalent": asdict(dens),
        "fit_coefficient_for_family_Fswirl_rhoratio_speed7": (
            F_GR_REF/(F_SWIRL_MAX*(RHO_CORE/RHO_F)*(C/VSWIRL)**7)
        ),
        "candidate_coefficient_16_over_pi2": 16.0/math.pi**2,
        "coefficient_ratio_candidate_over_fit": (
            (16.0/math.pi**2) /
            (F_GR_REF/(F_SWIRL_MAX*(RHO_CORE/RHO_F)*(C/VSWIRL)**7))
        ),
        "top25_scan": top25,
    }

    json_path = Path(prefix + ".json")
    txt_path = Path(prefix + ".txt")
    csv_path = Path(prefix + "_top25.csv")

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(top25[0].keys()))
        writer.writeheader()
        writer.writerows(top25)

    lines = []
    lines.append("Route D maximum-tension trial")
    lines.append("="*72)
    lines.append(f"F_gr_ref = c^4/(4G) = {F_GR_REF:.12e} N")
    lines.append(f"t_p_ref  = {T_P_REF:.12e} s")
    lines.append("")
    lines.append("Main candidate:")
    lines.append(f"  {main.expression}")
    lines.append(f"  F_D1        = {main.F_N:.12e} N")
    lines.append(f"  F_D1/F_ref  = {main.ratio:.12f}")
    lines.append(f"  rel error   = {main.rel_error:.12e}")
    lines.append(f"  t_p(D1)     = {main.t_p_s:.12e} s")
    lines.append(f"  t_p(D1)/tp  = {main.t_p_ratio:.12f}")
    lines.append("")
    lines.append("Density-equivalent candidate:")
    lines.append(f"  {dens.expression}")
    lines.append(f"  F_D1_density = {dens.F_N:.12e} N")
    lines.append(f"  ratio        = {dens.ratio:.12f}")
    lines.append("")
    lines.append("Coefficient audit:")
    K_fit = payload["fit_coefficient_for_family_Fswirl_rhoratio_speed7"]
    K_cand = payload["candidate_coefficient_16_over_pi2"]
    lines.append(f"  K_fit for F_swirl*rho_ratio*(c/v)^7 = {K_fit:.12f}")
    lines.append(f"  16/pi^2                                 = {K_cand:.12f}")
    lines.append(f"  candidate/fit                            = {K_cand/K_fit:.12f}")
    lines.append("")
    lines.append("Top 10 scan candidates:")
    for i, row in enumerate(top25[:10], start=1):
        lines.append(
            f"{i:02d}. ratio={row['ratio']:.12f}, rel={row['rel_error']:+.4e}, "
            f"{row['formula_family']}"
        )

    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return json_path, txt_path, csv_path

if __name__ == "__main__":
    write_outputs()
