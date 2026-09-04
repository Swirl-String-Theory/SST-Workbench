
from __future__ import annotations
import math, json
from pathlib import Path
from .common import dump_json

# Canonical values under audit
rho_core = 3.8934358266918687e18
v = 1.09384563e6
r_c = 1.40897017e-15
F = 29.053507
alpha = 7.2973525643e-3
c = 299792458.0
h = 6.62607015e-34
hbar = h/(2*math.pi)

def main(out="outputs/provenance_audit.json"):
    Jc = rho_core*v*r_c**4
    H_from_sst = 4*math.pi**2*Jc

    v_from_alpha = c*alpha/2
    F_from_hbar = v*hbar/(2*r_c**2)
    rho_from_F = 4*F/(math.pi*alpha**2*c**2*r_c**2)

    # Algebraic closure if legacy definitions are adopted:
    # rho = 4F/(pi alpha^2 c^2 r_c^2)
    # F   = v hbar/(2 r_c^2)
    # v   = alpha c/2
    # => 4 pi^2 rho v r_c^4 = 2 pi hbar = h.
    result = {
        "version": "SST-WP-PROVENANCE-1.0",
        "canonical": {
            "rho_core_kg_m3": rho_core,
            "v_m_s": v,
            "r_c_m": r_c,
            "F_swirl_max_N": F,
            "alpha": alpha,
            "c_m_s": c,
            "h_J_s": h,
            "hbar_J_s": hbar
        },
        "direct_numeric_relation": {
            "Jc_rho_v_rc4_J_s": Jc,
            "4pi2_Jc_J_s": H_from_sst,
            "ratio_to_h": H_from_sst/h,
            "relative_error": H_from_sst/h - 1.0,
            "2pi_Jc_J_s": 2*math.pi*Jc,
            "ratio_2piJc_to_hbar": (2*math.pi*Jc)/hbar
        },
        "legacy_dependency_checks": {
            "v_from_c_alpha_over_2_m_s": v_from_alpha,
            "v_ratio": v_from_alpha/v,
            "F_from_v_hbar_over_2rc2_N": F_from_hbar,
            "F_ratio": F_from_hbar/F,
            "rho_from_4F_over_pi_alpha2_c2_rc2": rho_from_F,
            "rho_ratio": rho_from_F/rho_core
        },
        "symbolic_dependency_chain": [
            "v = c alpha / 2",
            "F_swirl_max = v hbar / (2 r_c^2)",
            "rho_core = 4 F_swirl_max / (pi alpha^2 c^2 r_c^2)",
            "therefore 4 pi^2 rho_core v r_c^4 = h exactly"
        ],
        "classification": {
            "status": "PARAMETER_ECHO_IF_LEGACY_CHAIN_IS_DEFINING",
            "independent_prediction": False,
            "reason": "hbar enters F_swirl_max and propagates into rho_core; with v=c alpha/2 the target identity is algebraic."
        },
        "important_action_convention": {
            "planck_frequency_form": "DeltaE = h f",
            "angular_frequency_form": "DeltaE = hbar omega",
            "Jc_relation": "Jc = rho_core v r_c^4 = h/(4 pi^2) = hbar/(2 pi)",
            "warning": "Jc itself is not the Planck action quantum. A dynamic gate must measure DeltaE/f or DeltaE/omega directly."
        }
    }
    dump_json(out, result)
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else "outputs/provenance_audit.json"))
