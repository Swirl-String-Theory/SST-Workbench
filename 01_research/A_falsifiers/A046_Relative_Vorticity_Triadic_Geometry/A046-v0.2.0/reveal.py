from pathlib import Path
import json
import math
from sst_triadic.campaign import verify_seal
from sst_triadic.rotating import coriolis_parameter, rossby_number
from sst_triadic.reveal_constants import (
    C, V_CIRCLEARROW, R_C, RHO_F, F_SWIRL_MAX, F_GR_MAX, OMEGA_EARTH
)

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "A046_Relative_Vorticity_Triadic_Geometry_Falsifier_v0.2.0-outputs"
BLIND = BASE / "BLIND"
OUT = BASE / "REVEALED"
OUT.mkdir(parents=True, exist_ok=True)

ok, errors = verify_seal(BLIND)
if not ok:
    raise SystemExit("Blind seal verification failed: " + "; ".join(errors))

py_summary = json.loads((BLIND / "python_backend" / "blind_summary.json").read_text(encoding="utf-8"))
native_summary_path = BLIND / "native_backend" / "blind_summary.json"
parity_path = BLIND / "backend_parity_summary.json"

native_summary = None
parity = None
if native_summary_path.exists():
    native_summary = json.loads(native_summary_path.read_text(encoding="utf-8"))
if parity_path.exists():
    parity = json.loads(parity_path.read_text(encoding="utf-8"))

beta = V_CIRCLEARROW / C
clock = math.sqrt(1.0 - beta * beta)
n_gamma = 1.0 / clock
delta_n_exact = n_gamma - 1.0
delta_p = -0.5 * RHO_F * V_CIRCLEARROW ** 2
delta_n_leading = -delta_p / (RHO_F * C ** 2)
gamma0 = 2.0 * math.pi * R_C * V_CIRCLEARROW
omega_v_over_r = V_CIRCLEARROW / R_C
tau_r_over_v = R_C / V_CIRCLEARROW

f_north_pole = coriolis_parameter(OMEGA_EARTH, math.pi / 2.0)
f_south_pole = coriolis_parameter(OMEGA_EARTH, -math.pi / 2.0)

# Illustrative scale comparison only; not a gate and not an SST prediction.
scenarios = [
    ("illustrative_hurricane_core", 50.0, 1.0e5),
    ("illustrative_hurricane_outer", 50.0, 5.0e5),
    ("illustrative_tornado_core", 50.0, 1.0e3),
]
rossby = {
    name: {
        "U_m_s": U,
        "L_m": L,
        "Ro_at_pole": rossby_number(U, L, f_north_pole),
    }
    for name, U, L in scenarios
}

native_qualified = (
    native_summary is not None
    and native_summary.get("overall_status") == "PIPELINE_QUALIFIED"
    and parity is not None
    and parity.get("status") == "PASS"
)
release_mode = "FULL_PYTHON_NATIVE_QUALIFIED" if native_qualified else "PYTHON_REFERENCE_ONLY"

revealed = {
    "catalog_id": "A046",
    "version": "v0.2.0",
    "blind_seal_verified": True,
    "release_mode": release_mode,
    "python_blind_overall_status": py_summary["overall_status"],
    "native_blind_overall_status": (
        native_summary["overall_status"] if native_summary is not None else None
    ),
    "backend_parity_status": parity.get("status") if parity is not None else None,
    "candidate_basis": py_summary["candidate_basis"],
    "canonical_scale_check": {
        "c_m_s": C,
        "v_circlearrow_m_s": V_CIRCLEARROW,
        "r_c_m": R_C,
        "rho_f_kg_m3": RHO_F,
        "beta": beta,
        "swirl_clock": clock,
        "n_gamma_minus_1_exact": delta_n_exact,
        "delta_p_swirl_Pa": delta_p,
        "n_gamma_minus_1_leading": delta_n_leading,
        "leading_vs_exact_relative": abs(delta_n_exact - delta_n_leading) / delta_n_exact,
        "Gamma0_m2_s": gamma0,
        "v_over_r_characteristic_s-1": omega_v_over_r,
        "r_over_v_characteristic_s": tau_r_over_v,
        "F_swirl_max_N": F_SWIRL_MAX,
        "F_gr_max_N": F_GR_MAX,
        "force_ratio": F_SWIRL_MAX / F_GR_MAX,
    },
    "orthodox_rotating_frame_benchmark": {
        "omega_earth_rad_s": OMEGA_EARTH,
        "f_north_pole_s-1": f_north_pole,
        "f_south_pole_s-1": f_south_pole,
        "rossby_examples": rossby,
        "guard": (
            "Rossby examples use explicitly declared illustrative U and L values. "
            "They are scale diagnostics, not fitted atmospheric predictions."
        ),
    },
    "interpretation": (
        "Reveal values were evaluated only after the complete blind evidence tree was sealed. "
        "No canonical SST value or Earth rotation value was used to choose blind gates or tolerances."
    ),
}
(OUT / "reveal_summary.json").write_text(json.dumps(revealed, indent=2), encoding="utf-8")

lines = [
    "# A046 v0.2.0 reveal report",
    "",
    "Blind seal: **VERIFIED**",
    f"Release mode: **{release_mode}**",
    f"Python blind status: **{py_summary['overall_status']}**",
    f"Native blind status: **{revealed['native_blind_overall_status']}**",
    f"Backend parity: **{revealed['backend_parity_status']}**",
    "",
    f"HWC basis: **{py_summary['candidate_basis']['HWC']}**",
    f"UWS basis: **{py_summary['candidate_basis']['UWS']}**",
    "",
    "## Canonical-scale reveal",
    "",
    f"- beta = {beta:.12e}",
    f"- Swirl-Clock = {clock:.12e}",
    f"- n_gamma - 1 (exact) = {delta_n_exact:.12e}",
    f"- delta p_swirl = {delta_p:.12e} Pa",
    f"- Gamma_0 = {gamma0:.12e} m^2 s^-1",
    f"- v/r_c characteristic = {omega_v_over_r:.12e} s^-1",
    f"- r_c/v characteristic = {tau_r_over_v:.12e} s",
    "",
    "## Rotating-frame reveal benchmark",
    "",
    f"- Earth f at north pole = {f_north_pole:.12e} s^-1",
    f"- Earth f at south pole = {f_south_pole:.12e} s^-1",
]
for name, vals in rossby.items():
    lines.append(f"- {name}: Ro = {vals['Ro_at_pole']:.6g} for U={vals['U_m_s']} m/s, L={vals['L_m']} m")
lines += ["", revealed["orthodox_rotating_frame_benchmark"]["guard"], "", revealed["interpretation"]]
(OUT / "reveal_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps(revealed, indent=2))
