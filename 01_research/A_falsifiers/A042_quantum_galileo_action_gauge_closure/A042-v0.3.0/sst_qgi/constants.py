import math

# SST canonical inputs. These remain available only for the LEGACY ECHO CONTROL.
# Provenance audit: this triplet is NOT independent of h/hbar in the legacy derivation chain.
V_SWIRL = 1.09384563e6
R_C = 1.40897017e-15
RHO_CORE = 3.8934358266918687e18
RHO_F = 7.0e-7

def legacy_h_echo() -> float:
    # CONTROL ONLY; not an independent prediction.
    return 4.0 * math.pi**2 * RHO_CORE * V_SWIRL * R_C**4

def legacy_hbar_echo() -> float:
    return legacy_h_echo() / (2.0 * math.pi)

def provenance_audit() -> dict:
    return {
        "classification": "ALGEBRAIC_ECHO_CONTROL",
        "independent_prediction": False,
        "reason": (
            "Legacy SST definitions contain hbar upstream: "
            "v_swirl=alpha*c/2, F_swirl_max=v_swirl*hbar/(2*r_c^2), "
            "rho_core=4*F_swirl_max/(pi*alpha^2*c^2*r_c^2). "
            "Substitution yields 4*pi^2*rho_core*v_swirl*r_c^4 = 2*pi*hbar = h exactly."
        ),
        "blind_use": "allowed as negative/provenance control only",
    }
