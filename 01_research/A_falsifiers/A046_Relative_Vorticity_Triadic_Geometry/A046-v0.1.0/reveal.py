from pathlib import Path
import json
import math
from sst_triadic.campaign import verify_seal
from sst_triadic.reveal_constants import (
    C, V_CIRCLEARROW, R_C, RHO_F, F_SWIRL_MAX, F_GR_MAX
)

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parents[1] / "SST_Relative_Vorticity_Triadic_Geometry_Falsifier_v0.1.0-outputs"
BLIND = BASE / "BLIND"
OUT = BASE / "REVEALED"
OUT.mkdir(parents=True, exist_ok=True)

ok, errors = verify_seal(BLIND)
if not ok:
    raise SystemExit("Blind seal verification failed: " + "; ".join(errors))

blind = json.loads((BLIND / "blind_summary.json").read_text(encoding="utf-8"))

beta = V_CIRCLEARROW / C
clock = math.sqrt(1.0 - beta * beta)
n_gamma = 1.0 / clock
delta_n_exact = n_gamma - 1.0
delta_p = -0.5 * RHO_F * V_CIRCLEARROW ** 2
delta_n_leading = -delta_p / (RHO_F * C ** 2)
gamma0 = 2.0 * math.pi * R_C * V_CIRCLEARROW

revealed = {
    "blind_seal_verified": True,
    "blind_overall_status": blind["overall_status"],
    "candidate_basis": blind["candidate_basis"],
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
        "F_swirl_max_N": F_SWIRL_MAX,
        "F_gr_max_N": F_GR_MAX,
        "force_ratio": F_SWIRL_MAX / F_GR_MAX,
    },
    "interpretation": (
        "Reveal values were evaluated only after blind hashes were sealed. "
        "No canonical value was used to tune the blind ansatz or gates."
    ),
}
(OUT / "reveal_summary.json").write_text(
    json.dumps(revealed, indent=2), encoding="utf-8"
)

lines = [
    "# A045 reveal report",
    "",
    "Blind seal: **VERIFIED**",
    "",
    f"Blind numerical status: **{blind['overall_status']}**",
    "",
    f"HWC basis: **{blind['candidate_basis']['HWC']}**",
    "",
    f"UWS basis: **{blind['candidate_basis']['UWS']}**",
    "",
    "## Canonical scale evaluation",
    "",
    f"- beta = {beta:.12e}",
    f"- Swirl-Clock = {clock:.12e}",
    f"- n_gamma - 1 (exact) = {delta_n_exact:.12e}",
    f"- delta p_swirl = {delta_p:.12e} Pa",
    f"- n_gamma - 1 (leading pressure lock) = {delta_n_leading:.12e}",
    f"- Gamma_0 = {gamma0:.12e} m^2 s^-1",
    f"- F_swirl_max / F_gr_max = {F_SWIRL_MAX/F_GR_MAX:.12e}",
    "",
    "These values were inserted after the blind result was sealed.",
]
(OUT / "reveal_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps(revealed, indent=2))
