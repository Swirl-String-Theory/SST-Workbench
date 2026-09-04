"""Apply user-authoritative A_falsifiers chronology (A001-A042) across planning artifacts."""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLAN = Path(__file__).resolve().parent
CATALOG = PLAN / "CATALOG_v0.1.md"
RESTRUCTURE_PLAN = PLAN / "RESTRUCTURE_PLAN_v0.1.plan.md"
PATH_MAP = ROOT / "10_docs" / "migration" / "path_map.csv"
EPIC = PLAN / "RESTRUCTURE_EPIC.plan.md"

# User-authoritative A table with locations / official names
A_FALSIFIERS = [
    ("A001", "route_a_parallel_derivation_falsification", "SST v0.8.19 Route-A Parallel Derivation Falsification", "SST_v0_8_19_routes_research/..._RouteA_*", "2026-07-06", "confirmed"),
    ("A002", "nonfit_prediction_routes_control", "SST Non-Fit Prediction Harness (routes control)", "SST_v0_8_19_routes_research/sst_nonfit_*", "2026-07-07", "confirmed"),
    ("A003", "dark_knot_rayleigh", "SST Dark-Knot Rayleigh / Rocking Audit", "SST_dark_knot_rayleigh_research/", "2026-07-08", "confirmed"),
    ("A004", "dimensionless_dynamic_predictions", "SST Dimensionless Dynamic Predictions", "SST_dimensionless_dynamic_predictions/", "2026-08-01", "confirmed"),
    ("A005", "finite_core_c2", "Finite-Core c2 Archive-Only Falsifier (reserved)", "(archive-only; no working-tree package)", "2026-08-01", "reserved"),
    ("A006", "contact_billiard_hydrodynamic", "SST Contact Billiard Hydrodynamic Falsifier", "SST_contact_billiard_hydrodynamic_falsifier/", "2026-08-01", "confirmed"),
    ("A007", "ideal_links_topology_robustness", "SST Ideal Links Comprehensive Test Suite", "SST_ideal_links/", "2026-08-04", "confirmed"),
    ("A008", "chiral_kelvin_core", "SST Chiral Kelvin Mode Falsification", "SST_Chiral-Kelvin-Mode/", "2026-08-07", "confirmed"),
    ("A009", "preferred_frame_binary", "SST Preferred Frame Binary Falsifier", "SST_preferred_frame_binary_falsifier/", "2026-08-07", "confirmed"),
    ("A010", "counterpulley_alpha_ropelength", "SST Counterpulley Alpha Falsifier", "SST_counterpulley_alpha_falsifier/", "2026-08-10", "confirmed"),
    ("A011", "maxwell_1_kinetic_energy", "Maxwell SST Kinetic Falsifier", "SST_Maxwell/1_Maxwell_SST_Kinetic_*", "2026-08-13", "confirmed"),
    ("A012", "maxwell_3_physical_lines", "Maxwell SST Physical Lines / Blind Falsifier", "`SST_Maxwell/3_Maxwell_SST_Physical_Lines_*` + `SST_Maxwell/3_SST_Maxwell_Blind_*`", "2026-08-13", "confirmed"),
    ("A013", "maxwell_4_field_null", "SST Maxwell Falsifier (field null)", "SST_Maxwell/4_SST_Maxwell_Falsifier_*", "2026-08-13", "confirmed"),
    ("A014", "maxwell_5_reciprocal_figures", "Maxwell SST Reciprocal Falsifier", "SST_Maxwell/5_*_Reciprocal_*", "2026-08-13", "confirmed"),
    ("A015", "maxwell_2_dynamical_field", "Maxwell SST Dynamical Field Closure Falsifier", "SST_Maxwell/2_Maxwell_SST_Dynamical_*", "2026-08-13", "confirmed"),
    ("A016", "helmholtz_vortex_transport", "Helmholtz SST Vortex Gates Falsifier", "SST_Helmholtz/", "2026-08-13", "confirmed"),
    ("A017", "einstein_emergent_metric_poisson", "Einstein SST Emergent Metric Poisson Closure Gates", "SST_Einstein/Einstein_SST_Emergent_Metric_*", "2026-08-13", "confirmed"),
    ("A018", "einstein_blind", "Einstein SST Blind Falsifier", "SST_Einstein/Einstein_SST_Blind_Falsifier_*", "2026-08-13", "confirmed"),
    ("A019", "kelvin_kirchhoff_evanescent_core", "Kelvin Kirchhoff SST Falsifier", "SST_Kelvin_Floquet/Kelvin_Kirchhoff_*", "2026-08-18", "confirmed"),
    ("A020", "six_source_blind_energy", "SST 6-Source Blind Falsifier", "SST_6Source_Blind_Falsifier_v0.1.0/", "2026-08-18", "confirmed"),
    ("A021", "trefoil_lobe_self_confinement", "SST Trefoil Lobe Orientation Blind Falsifier", "SST_Trefoil_Lobe_Orientation_Blind_Falsifier/SST_Trefoil_Lobe_*", "2026-08-19", "confirmed"),
    ("A022", "fourier_vs_ideal", "SST Fourier vs Ideal Blind Falsifier", "SST_Fourier_vs_Ideal_Blind_Falsifier/", "2026-08-19", "confirmed"),
    ("A023", "multitopology_rpo_floquet", "SST MultiTopology Knot Link TBK RPO Falsifier", "SST_Trefoil_Lobe_.../SST_MultiTopology_*", "2026-08-20", "confirmed"),
    ("A024", "threaded_hole_separatrix", "SST Threaded Hole Substrate Blind Falsifier", "SST_Threaded_Hole_..._v0.1.0/SST_Threaded_Hole_*", "2026-08-20", "confirmed"),
    ("A025", "local_thread_texture_boost", "SST Local Thread Texture Boost Invariance Blind Falsifier", "SST_Threaded_Hole_..._v0.1.0/SST_Local_Thread_*", "2026-08-20", "confirmed"),
    ("A026", "phase_feedback_delay_knot_stability", "SST Phase Feedback Delay Knot Stability Blind Falsifier", "SST_Phase_Feedback_Delay_Knot_Stability/", "2026-08-21", "confirmed"),
    ("A027", "spectral_swirl_clock", "SST vArrow Spectral Blind Falsifier", "SST_vArrow_Spectral_Blind_Falsifier/", "2026-08-21", "confirmed"),
    ("A028", "seven_article_closure_holonomy", "SST 7-Article Closure Holonomy Blind Falsifier", "SST_7Article_Closure_Holonomy/", "2026-08-21", "confirmed"),
    ("A029", "finite_core_axial_toroidal_phase_delay", "SST Finite Core Axial Toroidal Phase Delay Blind Falsifier", "SST_Finite_Core_Axial_Toroidal_Phase_Delay/", "2026-08-21", "confirmed"),
    ("A030", "material_phase_eft_holonomy", "SST Material Phase EFT Falsifier", "SST_Material_Phase_EFT/", "2026-08-24", "confirmed"),
    ("A031", "adaptive_period_rpo_floquet", "SST Adaptive Period-Aware RPO Multiple Shooting Floquet Blind Falsifier", "SST_Trefoil_Lobe_.../SST_Adaptive_Period_*", "2026-08-24", "confirmed"),
    ("A032", "kelvin_joule_transient_energy", "Kelvin Joule SST Transient Energy Falsifier", "SST_Kelvin_Floquet/Kelvin_Joule_*", "2026-08-24", "confirmed"),
    ("A033", "breathing_stretching_return_phase", "SST Breathing Stretching Return Phase Causality Blind Falsifier", "SST_Breathing_Stretching_Return_Phase_Causality/", "2026-08-27", "confirmed"),
    ("A034", "qhp_stability_landscape", "SST QHP Stability Landscape Blind Falsifier", "SST_QHP_Stability_Landscape/SST_QHP_*", "2026-08-27", "confirmed"),
    ("A035", "intrinsic_modal_swirl_clock", "SST Intrinsic Modal Swirl Clock Blind Falsifier", "SST_Intrinsic_Modal_Swirl_Clock/SST_Intrinsic_*", "2026-08-27", "confirmed"),
    ("A036", "scii_intrinsic_modal_phase_clock", "SST SCII Intrinsic Modal Phase Swirl Clock Blind Falsifier", "SST_Intrinsic_Modal_Swirl_Clock/SST_SCII_*", "2026-08-28", "confirmed"),
    ("A037", "chirality_helicity_transport_polarity", "SST Chirality Helicity Transport Polarity Falsifier", "SST_Chirality_Helicity_Transport_Polarity/", "2026-08-28", "confirmed"),
    ("A038", "trefoil_dynamic_seed_qualification", "SST Trefoil Dynamic Seed Qualification Mega Falsifier", "SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier/", "2026-08-28", "confirmed"),
    ("A039", "sciib_frozen_modal_pair_phase_clock", "SST SCIIb Frozen Modal Pair Subspace Phase Clock Blind Falsifier", "SST_Intrinsic_Modal_Swirl_Clock/SST_SCIIb_*", "2026-08-28", "confirmed"),
    ("A040", "sciii_koopman_dmd_phase_clock", "SST SCIII Koopman DMD Complex Phase Clock Blind Falsifier", "SST_Intrinsic_Modal_Swirl_Clock/SST_SCIII_*", "2026-08-30", "confirmed"),
    ("A041", "wien_planck_field_matter_closure", "Wien-Planck SST Field Matter Closure Falsifier", "Wien_Planck_SST_Field_Matter_Closure/", "2026-09-03", "confirmed"),
    ("A042", "quantum_galileo_action_gauge_closure", "SST Quantum Galileo Action Gauge Closure Falsifier", "SST_Quantum_Galileo_Action_Gauge_Closure/", "2026-09-03", "confirmed"),
]

# old path_map / plan destinations -> new (by matching known old Axxx_slug prefixes)
# Built from previous CATALOG allocation.
OLD_TO_NEW_DEST = {
    "A001_contact_billiard_hydrodynamic": "A006_contact_billiard_hydrodynamic",
    "A002_dimensionless_dynamic_predictions": "A004_dimensionless_dynamic_predictions",
    "A003_minimal_falsification_harness": "D004_minimal_falsification_harness",
    "A004_sutcliffe_hss_feasibility_gate": "D005_sutcliffe_hss_feasibility_gate",
    "A005_chiral_kelvin_mode": "A008_chiral_kelvin_core",
    "A006_preferred_frame_binary": "A009_preferred_frame_binary",
    "A007_counterpulley_alpha": "A010_counterpulley_alpha_ropelength",
    "A008_einstein_blind": "A018_einstein_blind",
    "A009_einstein_emergent_metric_poisson_closure": "A017_einstein_emergent_metric_poisson",
    "A010_helmholtz_vortex_gates": "A016_helmholtz_vortex_transport",
    "A011_maxwell_kinetic": "A011_maxwell_1_kinetic_energy",
    "A012_maxwell_dynamical_field_closure": "A015_maxwell_2_dynamical_field",
    "A013_maxwell_physical_lines": "A012_maxwell_3_physical_lines",
    "A014_maxwell_blind": "A012_maxwell_3_physical_lines",
    "A015_maxwell_core": "A013_maxwell_4_field_null",
    "A016_maxwell_reciprocal": "A014_maxwell_5_reciprocal_figures",
    "A017_kelvin_kirchhoff": "A019_kelvin_kirchhoff_evanescent_core",
    "A018_six_source_blind": "A020_six_source_blind_energy",
    "A019_fourier_vs_ideal": "A022_fourier_vs_ideal",
    "A020_trefoil_lobe_orientation": "A021_trefoil_lobe_self_confinement",
    "A021_multitopology_knot_link_tbk_rpo": "A023_multitopology_rpo_floquet",
    "A022_threaded_hole_substrate": "A024_threaded_hole_separatrix",
    "A023_local_thread_texture_boost_invariance": "A025_local_thread_texture_boost",
    "A024_seven_article_closure_holonomy": "A028_seven_article_closure_holonomy",
    "A025_finite_core_axial_toroidal_phase_delay": "A029_finite_core_axial_toroidal_phase_delay",
    "A026_phase_feedback_delay_knot_stability": "A026_phase_feedback_delay_knot_stability",
    "A027_varrow_spectral": "A027_spectral_swirl_clock",
    "A028_kelvin_joule_transient_energy": "A032_kelvin_joule_transient_energy",
    "A029_material_phase_eft": "A030_material_phase_eft_holonomy",
    "A030_adaptive_period_aware_rpo_floquet": "A031_adaptive_period_rpo_floquet",
    "A031_breathing_stretching_return_phase_causality": "A033_breathing_stretching_return_phase",
    "A032_intrinsic_modal_swirl_clock": "A035_intrinsic_modal_swirl_clock",
    "A033_qhp_stability_landscape": "A034_qhp_stability_landscape",
    "A034_scii_intrinsic_modal_phase_swirl_clock": "A036_scii_intrinsic_modal_phase_clock",
    "A035_sciib_frozen_modal_pair_subspace_phase_clock": "A039_sciib_frozen_modal_pair_phase_clock",
    "A036_chirality_helicity_transport_polarity": "A037_chirality_helicity_transport_polarity",
    "A037_trefoil_dynamic_seed_qualification": "A038_trefoil_dynamic_seed_qualification",
    "A038_sciii_koopman_dmd_complex_phase_clock": "A040_sciii_koopman_dmd_phase_clock",
    "A039_quantum_galileo_action_gauge_closure": "A042_quantum_galileo_action_gauge_closure",
    "A040_wien_planck_field_matter_closure": "A041_wien_planck_field_matter_closure",
    # cascades into A from other letters
    "B005_route_a_parallel_derivation": "A001_route_a_parallel_derivation_falsification",
    "F005_nonfit_prediction_harness": "A002_nonfit_prediction_routes_control",
    "F006_dark_knot_rayleigh": "A003_dark_knot_rayleigh",
    "D003_ideal_links_test_suite": "A007_ideal_links_topology_robustness",
}

# catalog_id only remaps for path_map catalog_id column when domain is research A
ID_ONLY = {k.split("_", 1)[0]: v.split("_", 1)[0] for k, v in OLD_TO_NEW_DEST.items()}


def rewrite_catalog_a(md: str) -> str:
    rows = []
    for cid, slug, official, loc, date, status in A_FALSIFIERS:
        loc_cell = loc if "`" in loc else f"`{loc}`"
        rows.append(
            f"| {cid} | `{slug}` | {official} | {loc_cell} | {date} | {status} |"
        )
    table = "\n".join(
        [
            "| ID | Family | Official name | Current location | First version | Status |",
            "|----|--------|---------------|------------------|---------------|--------|",
            *rows,
        ]
    )
    note = """
**A005 is reserved.** `finite_core_c2` is an archive-only falsifier with no working-tree
package in the current inventory; no filesystem move is generated for it.

**A012 holds both Maxwell `3_` packs.** `3_Maxwell_SST_Physical_Lines_*` and
`3_SST_Maxwell_Blind_*` (plus their unblind keys as variants) share one catalog identity.

**Reveal keys are not families.** Maxwell and Galileo reveal/unblind keys are *variants* of a
version and live inside their family. They never get their own catalog ID. See SP06 §Reveal keys.

**Moved out of A in this chronology.** `SST_minimal_falsification_harness` and
`SST_Sutcliffe_HSS_feasibility_gate` are metrology/gates under `D_benchmarks` (D004, D005), not
hypothesis-bearing A falsifiers. `route_a`, `nonfit`, `dark_knot_rayleigh` and `ideal_links`
moved *into* A (A001–A003, A007).
"""
    pattern = re.compile(
        r"(## A_falsifiers — formal SST falsifiers and gates\n\n)"
        r".*?"
        r"(?=\n## B_closures)",
        re.S,
    )
    repl = r"\1" + table + "\n" + note + "\n"
    new_md, n = pattern.subn(repl, md, count=1)
    if n != 1:
        raise SystemExit(f"A_falsifiers section replace failed (n={n})")
    return new_md


def rewrite_catalog_b_f_d(md: str) -> str:
    # Remove B005 route_a; renumber B006-B008 -> B005-B007
    md = md.replace(
        "| B005 | `route_a_parallel_derivation` | SST v0.8.19 Route-A Parallel Derivation Falsification | `SST_v0_8_19_routes_research/..._RouteA_*` | 2026-07-06 | confirmed |\n",
        "",
    )
    md = md.replace("| B006 | `horn_dirichlet_bem`", "| B005 | `horn_dirichlet_bem`")
    md = md.replace("| B007 | `horn_neumann_bem`", "| B006 | `horn_neumann_bem`")
    md = md.replace("| B008 | `ssdl_audit`", "| B007 | `ssdl_audit`")

    # D: ideal_links -> A007; hopf cpp stays; add minimal + sutcliffe
    md = md.replace(
        "| D003 | `ideal_links_test_suite` | SST Ideal Links Comprehensive Test Suite | `SST_ideal_links/` | 2026-08-04 | confirmed |\n| D004 | `hopf_cpp_pybind` | SST Hopf Charge / Spin-Route Gate (C++/pybind) | `SST_Hopf_Benchmark/SST_Hopf_cpp_pybind_*` | 2026-08-07 | confirmed |\n",
        "| D003 | `hopf_cpp_pybind` | SST Hopf Charge / Spin-Route Gate (C++/pybind) | `SST_Hopf_Benchmark/SST_Hopf_cpp_pybind_*` | 2026-08-07 | confirmed |\n"
        "| D004 | `minimal_falsification_harness` | SST Minimal Falsification Harness | `SST_minimal_falsification_harness/` | 2026-08-01 | confirmed |\n"
        "| D005 | `sutcliffe_hss_feasibility_gate` | SST Sutcliffe HSS Feasibility Gate | `SST_Sutcliffe_HSS_feasibility_gate/` | 2026-08-03 | confirmed |\n",
    )

    # F: remove nonfit + dark_knot; renumber
    md = md.replace(
        "| F005 | `nonfit_prediction_harness` | SST Non-Fit Prediction Harness | `SST_v0_8_19_routes_research/sst_nonfit_*` | 2026-07-07 | confirmed |\n| F006 | `dark_knot_rayleigh` | SST Dark-Knot Rayleigh / Rocking Audit | `SST_dark_knot_rayleigh_research/` | 2026-07-08 | confirmed |\n| F007 | `route_i_relative_entropy`",
        "| F005 | `route_i_relative_entropy`",
    )
    md = md.replace("| F008 | `contra_swirl_bridge`", "| F006 | `contra_swirl_bridge`")
    md = md.replace("| F009 | `taxonomy_starter`", "| F007 | `taxonomy_starter`")
    md = md.replace("| F010 | `sycl_probes`", "| F008 | `sycl_probes`")
    return md


def rewrite_catalog_totals(md: str) -> str:
    # Update totals block
    md = re.sub(
        r"\| `01_research/A_falsifiers` \| 40 \|",
        "| `01_research/A_falsifiers` | 42 |",
        md,
    )
    md = re.sub(
        r"\| `01_research/B_closures` \| 8 \|",
        "| `01_research/B_closures` | 7 |",
        md,
    )
    md = re.sub(
        r"\| `01_research/D_benchmarks` \| 4 \|",
        "| `01_research/D_benchmarks` | 5 |",
        md,
    )
    md = re.sub(
        r"\| `01_research/F_exploratory` \| 10 \|",
        "| `01_research/F_exploratory` | 8 |",
        md,
    )
    # 40-1+3-2 wait: A 40->42 (+2 net: +4 into A -2 out to D, and A005 reserved counts)
    # research: A42 + B7 + C8 + D5 + E9 + F8 = 79
    # libraries4 + data16 + tools6 + apps4 = 30; total 109
    # Actually A005 reserved counts in catalog -> still 109 if we had 109 before with A40...
    # Before: 40+8+8+4+9+10+4+16+6+4 = 109
    # After: 42+7+8+5+9+8+4+16+6+4 = 109
    md = re.sub(
        r"109 catalog entries from 73 current roots: the container splits create 36 net new identities that\npreviously had no independent existence in the filesystem\.",
        "109 catalog entries from 73 current roots (A005 reserved has no move). "
        "A-falsifier IDs follow the chronological table frozen 2026-09-04.",
        md,
    )
    # Add chronology note at top of allocation
    if "A-falsifier chronology frozen" not in md:
        md = md.replace(
            "## Allocation rule\n",
            "## Allocation rule\n\n"
            "**A-falsifier chronology frozen 2026-09-04** to A001–A042 "
            "(earliest created timestamp; A005 reserved for archive-only `finite_core_c2`). "
            "This supersedes the interim A001=`contact_billiard` numbering.\n\n",
        )
    return md


def remap_path(text: str) -> str:
    # Longer keys first to avoid partial replaces
    for old, new in sorted(OLD_TO_NEW_DEST.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(old, new)
    return text


def rewrite_path_map() -> None:
    rows = list(csv.DictReader(PATH_MAP.open(encoding="utf-8")))
    fieldnames = list(rows[0].keys())
    out = []
    for row in rows:
        row["new_path"] = remap_path(row["new_path"])
        # catalog_id column
        cid = row.get("catalog_id") or ""
        # Special cases by old_path
        old = row["old_path"]
        if old.startswith("SST_v0_8_19_routes_research") and "RouteA" in old:
            row["catalog_id"] = "A001"
            row["domain"] = "01_research"
            row["letter"] = "A_falsifiers"
            row["new_path"] = remap_path(
                "01_research/A_falsifiers/A001_route_a_parallel_derivation_falsification"
                if "A001_" not in row["new_path"]
                else row["new_path"]
            )
        elif "nonfit" in old.lower():
            row["catalog_id"] = "A002"
            row["domain"] = "01_research"
            row["letter"] = "A_falsifiers"
        elif old.startswith("SST_dark_knot_rayleigh"):
            row["catalog_id"] = "A003"
            row["domain"] = "01_research"
            row["letter"] = "A_falsifiers"
            if "F006" in row["new_path"] or "F_exploratory" in row["new_path"]:
                row["new_path"] = "01_research/A_falsifiers/A003_dark_knot_rayleigh"
        elif old.startswith("SST_ideal_links"):
            row["catalog_id"] = "A007"
            row["domain"] = "01_research"
            row["letter"] = "A_falsifiers"
            row["new_path"] = "01_research/A_falsifiers/A007_ideal_links_topology_robustness"
        elif old.startswith("SST_minimal_falsification"):
            row["catalog_id"] = "D004"
            row["domain"] = "01_research"
            row["letter"] = "D_benchmarks"
            row["new_path"] = "01_research/D_benchmarks/D004_minimal_falsification_harness"
        elif old.startswith("SST_Sutcliffe"):
            row["catalog_id"] = "D005"
            row["domain"] = "01_research"
            row["letter"] = "D_benchmarks"
            row["new_path"] = "01_research/D_benchmarks/D005_sutcliffe_hss_feasibility_gate"
        elif cid in ID_ONLY and "A_falsifiers" in (row.get("letter") or "") or (
            cid.startswith("A") and row.get("letter") == "A_falsifiers"
        ):
            # extract new id from remapped path if present
            m = re.search(r"/(A\d{3})_", row["new_path"])
            if m:
                row["catalog_id"] = m.group(1)
        # F renumbers in path
        row["new_path"] = row["new_path"].replace(
            "F007_route_i_relative_entropy", "F005_route_i_relative_entropy"
        )
        row["new_path"] = row["new_path"].replace(
            "F008_contra_swirl_bridge", "F006_contra_swirl_bridge"
        )
        row["new_path"] = row["new_path"].replace(
            "F009_taxonomy_starter", "F007_taxonomy_starter"
        )
        row["new_path"] = row["new_path"].replace(
            "F010_sycl_probes", "F008_sycl_probes"
        )
        row["new_path"] = row["new_path"].replace(
            "B006_horn_dirichlet", "B005_horn_dirichlet"
        )
        row["new_path"] = row["new_path"].replace(
            "B007_horn_neumann", "B006_horn_neumann"
        )
        row["new_path"] = row["new_path"].replace(
            "B008_ssdl_audit", "B007_ssdl_audit"
        )
        row["new_path"] = row["new_path"].replace(
            "D004_hopf_cpp_pybind", "D003_hopf_cpp_pybind"
        )
        if row.get("catalog_id") == "F007":
            row["catalog_id"] = "F005"
        elif row.get("catalog_id") == "F008":
            row["catalog_id"] = "F006"
        elif row.get("catalog_id") == "F009":
            row["catalog_id"] = "F007"
        elif row.get("catalog_id") == "F010":
            row["catalog_id"] = "F008"
        elif row.get("catalog_id") == "B006":
            row["catalog_id"] = "B005"
        elif row.get("catalog_id") == "B007":
            row["catalog_id"] = "B006"
        elif row.get("catalog_id") == "B008":
            row["catalog_id"] = "B007"
        elif row.get("catalog_id") == "D004" and "hopf" in row["new_path"]:
            row["catalog_id"] = "D003"
        out.append(row)

    with PATH_MAP.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out)


def rewrite_plan_and_epic() -> None:
    for path in (RESTRUCTURE_PLAN, EPIC):
        text = path.read_text(encoding="utf-8")
        text = remap_path(text)
        text = text.replace(
            "`R/A/{A011,A012,A013,A014,A015,A016}`",
            "`R/A/{A011,A012,A013,A014,A015}`",
        )
        text = text.replace(
            "`R/A/{A032,A034,A035,A038}`",
            "`R/A/{A035,A036,A039,A040}`",
        )
        text = text.replace("`R/A/{A022,A023}`", "`R/A/{A024,A025}`")
        text = text.replace("`R/A/{A020,A021,A030}`", "`R/A/{A021,A023,A031}`")
        text = text.replace("`R/A/{A008,A009}`", "`R/A/{A017,A018}`")
        text = text.replace(
            "`R/A/{A017,A028}`, `R/C/C008`",
            "`R/A/{A019,A032}`, `R/C/C008`",
        )
        path.write_text(text, encoding="utf-8")


def main() -> None:
    md = CATALOG.read_text(encoding="utf-8")
    md = rewrite_catalog_a(md)
    md = rewrite_catalog_b_f_d(md)
    md = rewrite_catalog_totals(md)
    CATALOG.write_text(md, encoding="utf-8")
    print("Updated", CATALOG.name)

    rewrite_path_map()
    print("Updated", PATH_MAP)

    rewrite_plan_and_epic()
    print("Updated plan + epic via path remap")

    for sp in PLAN.glob("SP*.plan.md"):
        t = sp.read_text(encoding="utf-8")
        nt = remap_path(t)
        # Galileo examples (old interim ID A039 -> A042)
        nt = nt.replace('resolve_family("A039")', 'resolve_family("A042")')
        nt = nt.replace("resolve_family('A039')", "resolve_family('A042')")
        nt = nt.replace("catalog_id: A039", "catalog_id: A042")
        nt = nt.replace('"catalog_id": "A039"', '"catalog_id": "A042"')
        nt = nt.replace("A039-v0.1.1", "A042-v0.1.1")
        # Only the ellipsis form used for Galileo family in samples
        nt = nt.replace(
            "A039_quantum_galileo_action_gauge_closure",
            "A042_quantum_galileo_action_gauge_closure",
        )
        if nt != t:
            sp.write_text(nt, encoding="utf-8")
            print("Updated", sp.name)


if __name__ == "__main__":
    main()
