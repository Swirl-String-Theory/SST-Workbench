from pathlib import Path
import json

from sst_vortex_shear.campaign import verify_seal
from sst_vortex_shear.reveal_constants import (
    C, ALPHA, V_CIRCLEARROW, R_C, RHO_F, M_P_OVER_M_E,
    MASTER_CHI_ABS_TOL, PROTON_ELECTRON_REL_TOL,
)

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "A049_Isotropic_Euler_Vortex_Shear_Modulus_Falsifier_v0.4.1-outputs"
BLIND = BASE / "BLIND"
OUT = BASE / "REVEALED"
OUT.mkdir(parents=True, exist_ok=True)

ok, errors = verify_seal(BLIND)
if not ok:
    raise SystemExit("Blind seal verification failed: " + "; ".join(errors))

py = json.loads((BLIND / "python_backend" / "blind_summary.json").read_text(encoding="utf-8"))
native_path = BLIND / "native_backend" / "blind_summary.json"
parity_path = BLIND / "backend_parity_summary.json"
native = json.loads(native_path.read_text(encoding="utf-8")) if native_path.exists() else None
parity = json.loads(parity_path.read_text(encoding="utf-8")) if parity_path.exists() else None
release_mode = "FULL_PYTHON_NATIVE_QUALIFIED" if native is not None and parity is not None and parity.get("status") == "PASS" else "PYTHON_REFERENCE_ONLY"

wg = py["target_free_wave_hierarchy_gate"]
qualified = bool(wg["wave_qualified_before_any_external_target_comparison"])
chi = wg["chi_wave_if_qualified"]

chi_master_target = 0.5
chi_pe_target = C / (M_P_OVER_M_E * V_CIRCLEARROW)
master_factor_target = 4.0 / ALPHA

if qualified and chi is not None:
    chi = float(chi)
    cT = chi * V_CIRCLEARROW
    c_over_cT = C / cT
    mu = RHO_F * cT * cT
    master_chi_abs_error = abs(chi - chi_master_target)
    master_rel_error = abs(c_over_cT - master_factor_target) / master_factor_target
    pe_rel_error = abs(c_over_cT - M_P_OVER_M_E) / M_P_OVER_M_E
    master_gate = "PASS" if master_chi_abs_error <= MASTER_CHI_ABS_TOL else "FAIL"
    pe_gate = "PASS" if pe_rel_error <= PROTON_ELECTRON_REL_TOL else "FAIL"
else:
    cT = c_over_cT = mu = None
    master_chi_abs_error = master_rel_error = pe_rel_error = None
    master_gate = "NOT_REACHED_NO_QUALIFIED_BULK_WAVE_POLE"
    pe_gate = "NOT_REACHED_NO_QUALIFIED_BULK_WAVE_POLE"

revealed = {
    "catalog_id": "A049", "version": "v0.4.1", "blind_seal_verified": True,
    "release_mode": release_mode, "blind_pipeline_status": py["pipeline_status"],
    "research_question_status": py["research_question_status"],
    "canonical_constants": {
        "c_m_s": C, "alpha": ALPHA, "v_circlearrow_m_s": V_CIRCLEARROW,
        "r_c_m": R_C, "rho_f_kg_m3": RHO_F, "proton_electron_mass_ratio": M_P_OVER_M_E,
    },
    "wave_hierarchy_reveal": {
        "blind_wave_qualified": qualified,
        "chi_wave_cT_over_v_circlearrow": chi,
        "candidate_cT_m_s": cT,
        "candidate_mu_if_rho_eff_equals_rho_f_Pa": mu,
        "c_over_candidate_cT": c_over_cT,
        "master_factor": {
            "target_chi": chi_master_target,
            "target_c_over_cT": master_factor_target,
            "chi_absolute_tolerance": MASTER_CHI_ABS_TOL,
            "chi_absolute_error": master_chi_abs_error,
            "relative_c_over_cT_mismatch": master_rel_error,
            "status": master_gate,
        },
        "proton_electron_wave_hierarchy": {
            "target_mass_ratio": M_P_OVER_M_E,
            "equivalent_target_chi": chi_pe_target,
            "relative_tolerance": PROTON_ELECTRON_REL_TOL,
            "relative_mismatch": pe_rel_error,
            "status": pe_gate,
        },
    },
    "interpretation": (
        "v0.4.1 qualifies or rejects the transverse pole entirely in blind variables before any Master-Factor or proton/electron comparison. "
        "Reveal-only target comparisons cannot promote a noisy or absent pole. A passing mass-hierarchy comparison would therefore require a separately qualified approximately isotropic, helicity-degenerate, approximately linear bulk transverse mode."
    ),
}
(OUT / "reveal_summary.json").write_text(json.dumps(revealed, indent=2), encoding="utf-8")

lines = [
    "# A049 v0.4.1 reveal report", "", "Blind seal: **VERIFIED**",
    f"Release mode: **{release_mode}**", f"Pipeline: **{py['pipeline_status']}**",
    f"Research question: **{py['research_question_status']}**", "",
    "## Target-free pole qualification", "", f"- blind wave qualified = {qualified}",
    f"- chi_wave = {chi if chi is not None else 'NOT_REACHED'}", "",
    "## Master-Factor Wave Closure", "", f"- target chi = {chi_master_target:.12e}",
    f"- target c/c_T = 4/alpha = {master_factor_target:.12e}", f"- status = {master_gate}", "",
    "## Proton--Electron Wave-Hierarchy Gate", "",
    f"- target m_p/m_e = {M_P_OVER_M_E:.12e}", f"- equivalent target chi = {chi_pe_target:.12e}",
    f"- preregistered relative tolerance = {PROTON_ELECTRON_REL_TOL:.6e}", f"- status = {pe_gate}",
]
if qualified and chi is not None:
    lines += [
        "", "## Canonical wave-scale map", "", f"- c_T = {cT:.12e} m s^-1",
        f"- c/c_T = {c_over_cT:.12e}", f"- mu = {mu:.12e} Pa if rho_eff=rho_f",
        f"- Master relative mismatch = {master_rel_error:.12e}",
        f"- proton/electron relative mismatch = {pe_rel_error:.12e}",
    ]
lines += ["", "## Interpretation guard", "", revealed["interpretation"]]
(OUT / "reveal_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps(revealed, indent=2))
