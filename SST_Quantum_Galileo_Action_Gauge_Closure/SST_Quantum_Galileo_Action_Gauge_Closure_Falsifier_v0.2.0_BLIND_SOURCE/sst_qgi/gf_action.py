from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json, math

# Primary provenance-clean branch:
# Rankine solid-body vortex core, uniform mass density.
#
# For one tube of physical core radius a and centreline length L:
#   M_tube = rho * pi * a^2 * L
#
# The circulation enclosed at radius r is Gamma(r)=Gamma*(r/a)^2.
# Mass-weighting Gamma(r) over the cross-section gives
#   h_GF = (1/2) M_tube * Gamma
#
# The intrinsic angular momentum of the same Rankine core is
#   hbar_GF = (1/(4*pi)) M_tube * Gamma
#
# Therefore:
#   h_GF = 2*pi*hbar_GF
#
# These are candidate fluid action scales. Their identification with the
# quantum action scale is a falsifiable SST research hypothesis, not an
# orthodox theorem.

@dataclass(frozen=True)
class FluidProvenance:
    measurement_id: str
    gamma_m2_s: float
    sigma_gamma_m2_s: float | None
    status: str
    method: str
    source: str
    depends_on_h: bool
    depends_on_hbar: bool
    depends_on_compton_radius: bool
    depends_on_electron_mass: bool
    depends_on_alpha: bool

    @property
    def clean_for_specific_action(self) -> bool:
        return (
            self.status == "INDEPENDENT_MEASURED"
            and self.gamma_m2_s > 0
            and not self.depends_on_h
            and not self.depends_on_hbar
            and not self.depends_on_compton_radius
            and not self.depends_on_electron_mass
            and not self.depends_on_alpha
        )

def load_fluid_provenance(path: Path) -> FluidProvenance | None:
    path = Path(path)
    if not path.exists():
        return None
    obj = json.loads(path.read_text(encoding="utf-8"))
    return FluidProvenance(
        measurement_id=str(obj.get("measurement_id","")),
        gamma_m2_s=float(obj["Gamma_m2_s"]),
        sigma_gamma_m2_s=(
            None if obj.get("sigma_Gamma_m2_s") in (None,"")
            else float(obj["sigma_Gamma_m2_s"])
        ),
        status=str(obj.get("status","UNDECLARED")),
        method=str(obj.get("method","")),
        source=str(obj.get("source","")),
        depends_on_h=bool(obj.get("depends_on_h", True)),
        depends_on_hbar=bool(obj.get("depends_on_hbar", True)),
        depends_on_compton_radius=bool(obj.get("depends_on_compton_radius", True)),
        depends_on_electron_mass=bool(obj.get("depends_on_electron_mass", True)),
        depends_on_alpha=bool(obj.get("depends_on_alpha", True)),
    )

def rankine_specific_action(gamma_m2_s: float) -> dict:
    # No mass, density, core radius, h or hbar are needed.
    # Full-cycle specific action h/M has units m^2/s.
    h_over_m = 0.5 * gamma_m2_s
    hbar_over_m = gamma_m2_s / (4.0 * math.pi)
    return {
        "Gamma_m2_s": gamma_m2_s,
        "h_over_m_m2_s": h_over_m,
        "hbar_over_m_m2_s": hbar_over_m,
        "two_pi_identity_rel": abs(h_over_m/(2.0*math.pi*hbar_over_m)-1.0),
    }

def geometry_action_coefficients(length: float, thickness_radius: float) -> dict:
    if not (length > 0 and thickness_radius > 0 and math.isfinite(length) and math.isfinite(thickness_radius)):
        return {
            "qualified": False,
            "Lhat_radius": None,
            "mass_volume_coeff_pi_Lhat": None,
            "h_coeff_rho_Gamma_a3": None,
            "hbar_coeff_rho_Gamma_a3": None,
        }
    Lhat = length / thickness_radius
    # L = a * Lhat.
    # M = rho*pi*a^3*Lhat.
    # h_GF = 1/2*M*Gamma = (pi/2)*Lhat*rho*Gamma*a^3.
    # hbar_GF = h_GF/(2*pi) = (1/4)*Lhat*rho*Gamma*a^3.
    return {
        "qualified": True,
        "Lhat_radius": Lhat,
        "mass_volume_coeff_pi_Lhat": math.pi * Lhat,
        "h_coeff_rho_Gamma_a3": 0.5 * math.pi * Lhat,
        "hbar_coeff_rho_Gamma_a3": 0.25 * Lhat,
    }

def absolute_rankine_action(
    rho_kg_m3: float,
    gamma_m2_s: float,
    a_core_m: float,
    Lhat_radius: float,
) -> dict:
    M = rho_kg_m3 * math.pi * a_core_m**3 * Lhat_radius
    h = 0.5 * M * gamma_m2_s
    hbar = h/(2.0*math.pi)
    return {
        "tube_mass_kg": M,
        "h_GF_J_s": h,
        "hbar_GF_J_s": hbar,
        "h_over_M_m2_s": h/M,
        "hbar_over_M_m2_s": hbar/M,
    }

def load_absolute_fluid_scale(path: Path) -> dict | None:
    path = Path(path)
    if not path.exists():
        return None
    obj = json.loads(path.read_text(encoding="utf-8"))
    required = ("rho_kg_m3","a_core_m")
    if any(k not in obj for k in required):
        return None
    clean = (
        obj.get("status") == "INDEPENDENT_MEASURED"
        and not bool(obj.get("depends_on_h", True))
        and not bool(obj.get("depends_on_hbar", True))
        and not bool(obj.get("depends_on_compton_radius", True))
        and not bool(obj.get("depends_on_electron_mass", True))
        and not bool(obj.get("depends_on_alpha", True))
    )
    return {
        **obj,
        "rho_kg_m3": float(obj["rho_kg_m3"]),
        "a_core_m": float(obj["a_core_m"]),
        "clean_model_provenance": clean,
        "metrology_note": (
            "Any SI kg-based absolute action inherits the post-2019 SI definition of the kilogram via fixed h. "
            "Therefore the absolute branch can be model-provenance-clean but is not metrology-independent of h. "
            "The primary specific-action/circulation branch avoids kg entirely."
        ),
    }
