from __future__ import annotations
import math, json, sys
from . import reveal_constants as C
from .common import dump_json

def audit():
    v_def = C.c * C.alpha / 2
    F_def = C.v_swirl * C.hbar / (2 * C.r_c**2)
    rho_def = 4 * C.F_swirl_max / (
        math.pi * C.alpha**2 * C.c**2 * C.r_c**2
    )
    lhs = 4 * math.pi**2 * C.rho_core * C.v_swirl * C.r_c**4

    # If reveal normalization uses L=r_c, Gamma=2*pi*r_c*v and rho=rho_core:
    J0_legacy = C.rho_core * C.Gamma_c * C.r_c**3

    return {
        "format": "SST-WP-PROVENANCE-2.1",
        "classification":
            "PARAMETER_ECHO_IF_LEGACY_CHAIN_IS_DEFINING",
        "independent_prediction": False,
        "identity": "4*pi^2*rho_core*v_swirl*r_c^4 = h",
        "numeric": {
            "lhs_J_s": lhs,
            "h_J_s": C.h,
            "ratio": lhs / C.h,
            "relative_error": lhs / C.h - 1,
            "Jc_J_s": C.rho_core * C.v_swirl * C.r_c**4,
            "Jc_over_h": C.rho_core * C.v_swirl * C.r_c**4 / C.h,
        },
        "dependency_checks": {
            "v_from_alpha_c_over_2": v_def,
            "v_ratio": v_def / C.v_swirl,
            "F_from_v_hbar_over_2rc2": F_def,
            "F_ratio": F_def / C.F_swirl_max,
            "rho_from_F_alpha_c_rc": rho_def,
            "rho_ratio": rho_def / C.rho_core,
        },
        "symbolic_chain": [
            "v=alpha*c/2",
            "F=v*hbar/(2*r_c^2)",
            "rho_core=4F/(pi*alpha^2*c^2*r_c^2)",
            "therefore 4*pi^2*rho_core*v*r_c^4=2*pi*hbar=h",
        ],
        "legacy_reveal_normalization": {
            "definition": "J0 = rho*Gamma*L^3",
            "legacy_mapping": "rho=rho_core, Gamma=2*pi*r_c*v, L=r_c",
            "J0_J_s": J0_legacy,
            "ratio_to_hbar": J0_legacy / C.hbar,
            "classification":
                "CONTAMINATED_NORMALIZATION; hbar is algebraically embedded",
        },
        "action_path_rule":
            "v0.2.1 pre-reveal campaign/scoring uses only L_hat=1, "
            "Gamma_hat=1, core_fraction, geometry, and dimensionless numerical controls. "
            "All SST canonical constants and SI scales are forbidden until reveal.",
    }

def main(out="outputs/provenance_audit.json"):
    r = audit()
    dump_json(out, r)
    print(json.dumps(r, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(
        main(sys.argv[1] if len(sys.argv) > 1 else "outputs/provenance_audit.json")
    )
