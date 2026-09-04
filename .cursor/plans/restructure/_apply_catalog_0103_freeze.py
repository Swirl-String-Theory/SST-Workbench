"""Apply user 01/02/03 catalog freeze + DELETE/<relpath> soft-delete rule."""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLAN = Path(__file__).resolve().parent
CATALOG = PLAN / "CATALOG_v0.1.md"
PATH_MAP = ROOT / "10_docs" / "migration" / "path_map.csv"
EPIC = PLAN / "RESTRUCTURE_EPIC.plan.md"
SP11 = PLAN / "SP11_decommission.plan.md"
README = PLAN / "README.md"
RESTRUCTURE_PLAN = PLAN / "RESTRUCTURE_PLAN_v0.1.plan.md"

# Canonical research + library + data destinations (user table)
# old_path (exact or prefix) -> new_path
MOVES: list[tuple[str, str, str, str, str, str, str]] = [
    # old, new, domain, letter, catalog_id, kind, phase
    # --- data (no catalog IDs) ---
    ("Fremlin_FourierSeries", "03_data/A_knots/02_fourier/fremlin_fourier_series", "03_data", "A_knots", "", "data", "SP04"),
    ("Ideal_Sources", "03_data/A_knots/01_ideal/ideal_sources", "03_data", "A_knots", "", "data", "SP04"),
    ("Katlas_Sources_v0.2.2_Outputs", "03_data/A_knots/03_katlas/v0.2.2", "03_data", "A_knots", "", "data", "SP04"),
    ("media", "03_data/C_media", "03_data", "C_media", "", "data", "SP04"),
    ("generated-figures", "03_data/D_generated/figures", "03_data", "D_generated", "", "output", "SP04"),
    ("PTSA_Parametric_Trefoil_Seed_Atlas_v1.0.0", "01_research/E_pipelines/E009_ptsa_parametric_trefoil_seed_atlas", "01_research", "E_pipelines", "E009", "code", "SP05"),
    # datasets is a container — children mapped; root residual to DELETE if empty later
    ("datasets/SPARC", "03_data/B_external/SPARC", "03_data", "B_external", "", "data", "SP04"),
    ("datasets/resources-swirl/ideal_12_data", "03_data/A_knots/01_ideal/ideal_12_data", "03_data", "A_knots", "", "data", "SP04"),
    ("datasets/resources-swirl/Knots_FourierSeries", "03_data/A_knots/02_fourier/resources_swirl", "03_data", "A_knots", "", "data", "SP04"),
    ("datasets/twist_knots", "03_data/A_knots/05_twist_knots", "03_data", "A_knots", "", "data", "SP04"),
    ("datasets/exports", "03_data/D_generated/legacy_dataset_exports", "03_data", "D_generated", "", "output", "SP04"),
    ("datasets/resources-swirl/results", "03_data/D_generated/legacy_resources_swirl_results", "03_data", "D_generated", "", "output", "SP04"),
    # libraries
    ("Knot_Geometry_Library", "02_libraries/A_knot_libraries/A001_knot_geometry_library", "02_libraries", "A_knot_libraries", "A001", "code", "SP05"),
    ("Knot_Library", "02_libraries/A_knot_libraries/A002_knot_library", "02_libraries", "A_knot_libraries", "A002", "code", "SP06"),
    ("Independent_FiniteCore_SpectralSelector", "02_libraries/B_finite_core/B001_independent_finitecore_spectral_selector", "02_libraries", "B_finite_core", "B001", "code", "SP05"),
    # research A (keep existing A destinations — already correct)
    # research B
    ("SST_derive_constants_research", "01_research/B_closures/B001_derive_constants", "01_research", "B_closures", "B001", "code", "SP05"),
    ("SST_horn_bem_research", "01_research/B_closures/B003_horn_bem", "01_research", "B_closures", "B003", "code", "SP06"),
    ("SST_routeB_RT_bem_research", "01_research/B_closures/B004_route_b_rt_bem", "01_research", "B_closures", "B004", "code", "SP05"),
    ("SST_contra_swirl_bridge_research", "01_research/B_closures/B005_contra_swirl_bridge", "01_research", "B_closures", "B005", "code", "SP05"),
    # research C
    ("SST_chi_phase_research", "01_research/C_dynamics/C001_chi_phase_track_b", "01_research", "C_dynamics", "C001", "code", "SP06"),
    ("SST_ideal_trefoil_biot_research", "01_research/C_dynamics/C002_ideal_trefoil_biot", "01_research", "C_dynamics", "C002", "code", "SP06"),
    ("SST_fermat_pybind_research", "01_research/C_dynamics/C005_fermat_biot_savart", "01_research", "C_dynamics", "C005", "code", "SP05"),
    # research D
    ("verification-suites", "01_research/D_benchmarks/D003_verification_suites", "01_research", "D_benchmarks", "D003", "code", "SP05"),
    ("SST_fs_attachment_audit_research", "01_research/D_benchmarks/D002_fs_attachment_audit", "01_research", "D_benchmarks", "D002", "code", "SP05"),
    ("SST_ssdl_audit_research", "01_research/D_benchmarks/D004_ssdl_audit", "01_research", "D_benchmarks", "D004", "code", "SP05"),
    ("SST_Hopf_Benchmark", "01_research/D_benchmarks/D005_hopf_benchmark", "01_research", "D_benchmarks", "D005", "code", "SP06"),
    ("SST_minimal_falsification_harness", "01_research/D_benchmarks/D006_minimal_falsification_harness", "01_research", "D_benchmarks", "D006", "code", "SP05"),
    ("SST_Sutcliffe_HSS_feasibility_gate", "01_research/D_benchmarks/D007_sutcliffe_hss_feasibility_gate", "01_research", "D_benchmarks", "D007", "code", "SP05"),
    # research E
    ("SST21D_knot_order_pipeline", "01_research/E_pipelines/E001_sst21d_knot_order_pipeline", "01_research", "E_pipelines", "E001", "code", "SP05"),
    ("Trefoil_Balance_to_TBK_RPO_Handoff_v0.1.0", "01_research/E_pipelines/E005_trefoil_balance_to_tbk_rpo_handoff", "01_research", "E_pipelines", "E005", "code", "SP05"),
    ("SST_Katlas_Link_Geometry_Conditioning_v2.0.0", "01_research/E_pipelines/E008_katlas_link_geometry_conditioning", "01_research", "E_pipelines", "E008", "code", "SP05"),
    # research F
    ("SST_Coil_DigitalTwin_research", "01_research/F_exploratory/F001_coil_digital_twin", "01_research", "F_exploratory", "F001", "code", "SP05"),
    ("SST_Route_I_relative_entropy_PoC", "01_research/F_exploratory/F002_route_i_relative_entropy_poc", "01_research", "F_exploratory", "F002", "code", "SP06"),
    ("SST_CoilLab_research", "01_research/F_exploratory/F003_coil_lab", "01_research", "F_exploratory", "F003", "code", "SP05"),
    # timefield → generated
    ("SST_timefield_spectral_v06_research", "03_data/D_generated/research_outputs/timefield_spectral_v06", "03_data", "D_generated", "", "output", "SP05"),
    # 3D mesh data
    ("3D/3d-mesh", "03_data/D_generated/3d/meshes", "03_data", "D_generated", "", "output", "SP06"),
    # soft-deletes → DELETE/<original relative path>
    ("to_be_processed", "DELETE/to_be_processed", "DELETE", "", "", "stub", "SP11"),
    ("experiments/derive_constants", "DELETE/experiments/derive_constants", "DELETE", "", "", "stub", "SP11"),
    ("experiments/trefoil", "DELETE/experiments/trefoil", "DELETE", "", "", "stub", "SP11"),
    ("experiments/sycl", "04_tools/D_compute/sycl_probes", "04_tools", "D_compute", "", "tooling", "SP06"),
    ("falsifier_registry", "DELETE/falsifier_registry", "DELETE", "", "", "stub", "SP11"),
]

# A-family roots already correctly mapped — keep via overlay on existing path_map
A_KEEP_PREFIXES = (
    "SST_6Source_",
    "SST_7Article_",
    "SST_Breathing_",
    "SST_Chiral-",
    "SST_Chirality_",
    "SST_contact_billiard",
    "SST_counterpulley_",
    "SST_dark_knot_",
    "SST_dimensionless_",
    "SST_Finite_Core_Axial_",
    "SST_Fourier_vs_Ideal_",
    "SST_Helmholtz",
    "SST_ideal_links",
    "SST_Material_Phase_",
    "SST_Phase_Feedback_",
    "SST_preferred_frame_",
    "SST_Quantum_Galileo_",
    "SST_Trefoil_Dynamic_Seed_",
    "SST_vArrow_",
    "Wien_Planck_",
    "SST_Maxwell/",
    "SST_Einstein/",
    "SST_Kelvin_Floquet/Kelvin_",
    "SST_Trefoil_Lobe_",
    "SST_Threaded_Hole_",
    "SST_Intrinsic_Modal_",
    "SST_QHP_Stability_",
    "SST_6Source_Blind",
)

CATALOG_B_THROUGH_03 = r'''
## B_closures — closure and field-equation research

| ID | Family | Official name | Current location | First version | Status |
|----|--------|---------------|------------------|---------------|--------|
| B001 | `derive_constants` | SST Derive Constants Research | `SST_derive_constants_research/` | 2026-06-04 | confirmed |
| B002 | `planck_routes_a_to_d` | SST v0.8.19 Planck Routes A–D (+ v3 packs) | `SST_v0_8_19_routes_research/Planck_Routes_*` | 2026-07-06 | confirmed |
| B003 | `horn_bem` | SST Horn-Torus BEM (Dirichlet + Neumann) | `SST_horn_bem_research/` | 2026-07-07 | confirmed |
| B004 | `route_b_rt_bem` | SST Route-B R–T BEM Research | `SST_routeB_RT_bem_research/` | 2026-08-01 | confirmed |
| B005 | `contra_swirl_bridge` | SST Contra-Swirl Bridge | `SST_contra_swirl_bridge_research/` | 2026-08-01 | confirmed |

Planck A–D equivalence and v3-preregistered packs are **versions under B002**, not separate
families. Horn Dirichlet and Neumann packages are **subtrees under B003**.

## C_dynamics — vortex, finite-core and Floquet dynamics

| ID | Family | Official name | Current location | First version | Status |
|----|--------|---------------|------------------|---------------|--------|
| C001 | `chi_phase_track_b` | SST Chi-Phase Track B | `SST_chi_phase_research/sst_chi_phase_package_v10B1…v16B0` (+ Trefoil_Closure ancestors) | 2026-07-04 | confirmed |
| C002 | `ideal_trefoil_biot` | SST Ideal Trefoil Biot–Savart | `SST_ideal_trefoil_biot_research/` | 2026-07-06 | confirmed |
| C003 | `chie_local_biot_savart` | SSTcore ChiE Local Biot–Savart | `SST_chi_phase_research/sstcore_chiE_local_v4…v7` | 2026-07-06 | confirmed |
| C004 | `torsion_impedance` | SST Torsion Impedance pybind11 | `SST_v0_8_19_routes_research/sst_torsion_impedance_*` | 2026-07-07 | confirmed |
| C005 | `fermat_biot_savart` | SST Fermat-Metric / Biot–Savart Knot Diagnostics | `SST_fermat_pybind_research/` | 2026-07-28 | confirmed |
| C006 | `kelvin_floquet_workbench` | SST Kelvin Floquet Workbench (C++/pybind) | `SST_Kelvin_Floquet/SST_Kelvin_Floquet_Workbench_*` | 2026-08-10 | confirmed |

`sst_3d_collider_robust` and `sst_trefoil_bs` move with **C002** (no own catalog ID).
`GUI/additional for Vlab/` is handled in the GUI/apps split (SP06), not as a C-family.

## D_benchmarks — audits, verification and certification

| ID | Family | Official name | Current location | First version | Status |
|----|--------|---------------|------------------|---------------|--------|
| D001 | `schrodinger_gate_constants_audit` | SST Schrödinger Gate Constants Audit | `SST_derive_constants_research/schrodinger_gate/...` | 2026-06-25 | confirmed |
| D002 | `fs_attachment_audit` | SST Framed-Helicity / Attachment Audit | `SST_fs_attachment_audit_research/` | 2026-07-03 | confirmed |
| D003 | `verification_suites` | Embedded Knots / verification suites | `verification-suites/` | 2026-07-03 | confirmed |
| D004 | `ssdl_audit` | SST Separatrix Surface-Density Lift Audit | `SST_ssdl_audit_research/` | 2026-07-08 | confirmed |
| D005 | `hopf_benchmark` | SST Hopf Benchmark (packet + cpp_pybind) | `SST_Hopf_Benchmark/` | 2026-08-01 | confirmed |
| D006 | `minimal_falsification_harness` | SST Minimal Falsification Harness | `SST_minimal_falsification_harness/` | 2026-08-01 | confirmed |
| D007 | `sutcliffe_hss_feasibility_gate` | SST Sutcliffe HSS Feasibility Gate | `SST_Sutcliffe_HSS_feasibility_gate/` | 2026-08-03 | confirmed |
| D008 | `knotplot_missingparameter_certification` | KnotPlot 3p1 MissingParameter Command Certification | `KnotPlot/KnotPlot_3p1_MissingParameter_*` | 2026-08-24 | confirmed |
| D009 | `knotplot_parameter_atlas` | KnotPlot 3p1 Comprehensive Dynamics Parameter Atlas | `KnotPlot/KnotPlot_3p1_Comprehensive_Dynamics_Parameter_Atlas_*` | 2026-08-24 | confirmed |

## E_pipelines — dataset, knot and campaign pipelines

| ID | Family | Official name | Current location | First version | Status |
|----|--------|---------------|------------------|---------------|--------|
| E001 | `sst21d_knot_order_pipeline` | SST-21D Knot Order Pipeline | `SST21D_knot_order_pipeline/` | 2026-08-01 | confirmed |
| E002 | `knotplot_multidynamics_relaxation_matrix` | KnotPlot 3p1 MultiDynamics Relaxation Matrix | `KnotPlot/KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_*` | 2026-08-21 | confirmed |
| E003 | `knotplot_trefoil_seed_campaign` | KnotPlot 3p1 Trefoil Seed Campaign | `KnotPlot/KnotPlot_3p1_Trefoil_Seed_Campaign_*` | 2026-08-24 | confirmed |
| E004 | `trefoil_balance_point_campaign` | KnotPlot Trefoil Balance Point Campaign | `KnotPlot/Trefoil_Balance_Point_Campaign_*` | 2026-08-24 | confirmed |
| E005 | `trefoil_balance_to_tbk_rpo_handoff` | Trefoil Balance to TBK RPO Handoff | `Trefoil_Balance_to_TBK_RPO_Handoff_v0.1.0/` | 2026-08-24 | confirmed |
| E006 | `knotplot_multitopology_qhp_sweep` | KnotPlot MultiTopology QHP Sweep | `KnotPlot/KnotPlot_MultiTopology_QHP_Sweep_*` | 2026-08-25 | confirmed |
| E007 | `knotplot_qhp_sweep_generator` | SST KnotPlot QHP Sweep Generator | `SST_QHP_Stability_Landscape/SST_KnotPlot_QHP_Sweep_Generator_*` | 2026-08-27 | confirmed |
| E008 | `katlas_link_geometry_conditioning` | SST Katlas Link Geometry Conditioning | `SST_Katlas_Link_Geometry_Conditioning_v2.0.0/` | 2026-08-30 | confirmed |
| E009 | `ptsa_parametric_trefoil_seed_atlas` | Parametric Trefoil Seed Atlas | `PTSA_Parametric_Trefoil_Seed_Atlas_v1.0.0/` | 2026-09-03 | confirmed |

## F_exploratory — PoCs and not-yet-formalized research

| ID | Family | Official name | Current location | First version | Status |
|----|--------|---------------|------------------|---------------|--------|
| F001 | `coil_digital_twin` | SST Coil Digital Twin | `SST_Coil_DigitalTwin_research/` | 2026-06-26 | confirmed |
| F002 | `route_i_relative_entropy_poc` | SST Route-I Relative Entropy PoC | `SST_Route_I_relative_entropy_PoC/` | 2026-07-06 | confirmed |
| F003 | `coil_lab` | SST CoilLab | `SST_CoilLab_research/` | 2026-06-26 | confirmed |
| F004 | `taxonomy_starter` | SST Taxonomy Starter | `SST_Trefoil_Closure/sst_taxonomy_starter_*` | 2026-08-01 | provisional |

`routeI_heat_guard_*` is a **variant under F002**, not its own family.
`experiments/sycl` moves to `04_tools` (not F).

---

# 02_libraries

Letters are local to `02_libraries` (no clash with research A001).

| ID | Family | Official name | Current location | First version | Status |
|----|--------|---------------|------------------|---------------|--------|
| A001 | `knot_geometry_library` | SST Knot Geometry Library | `Knot_Geometry_Library/` | — | confirmed |
| A002 | `knot_library` | SST Knot Library | `Knot_Library/` | — | confirmed |
| B001 | `independent_finitecore_spectral_selector` | Independent Finite-Core Spectral Selector | `Independent_FiniteCore_SpectralSelector/` | — | confirmed |

```text
02_libraries/
├── A_knot_libraries/
│   ├── A001_knot_geometry_library/
│   └── A002_knot_library/
└── B_finite_core/
    └── B001_independent_finitecore_spectral_selector/
```

No `D_numerics` in this freeze; `sst_trefoil_bs` travels with C002.

---

# 03_data

**No per-dataset catalog IDs** unless a dataset later becomes a versioned product. Classification is provenance/type.

## A_knots

| Group | Current location | Destination |
|-------|------------------|-------------|
| Ideal 12 | `datasets/resources-swirl/ideal_12_data` | `03_data/A_knots/01_ideal/ideal_12_data` |
| Ideal Sources | `Ideal_Sources` | `03_data/A_knots/01_ideal/ideal_sources` |
| Fourier (resources-swirl) | `datasets/resources-swirl/Knots_FourierSeries` | `03_data/A_knots/02_fourier/resources_swirl` |
| Fremlin Fourier | `Fremlin_FourierSeries` | `03_data/A_knots/02_fourier/fremlin_fourier_series` |
| KnotPlot Fourier | `KnotPlot/Knots_FourierSeries` | `03_data/A_knots/02_fourier/knotplot_legacy` |
| KAtlas | `Katlas_Sources_v0.2.2_Outputs` | `03_data/A_knots/03_katlas/v0.2.2` |
| KnotPlot knots | `KnotPlot/knots` | `03_data/A_knots/04_knotplot` |
| Twist knots | `datasets/twist_knots` | `03_data/A_knots/05_twist_knots` |

## B_external

| Current | Destination |
|---------|-------------|
| `datasets/SPARC` | `03_data/B_external/SPARC` |

## C_media

| Current | Destination |
|---------|-------------|
| `media` | `03_data/C_media` |

## D_generated

| Current | Destination |
|---------|-------------|
| `3D/3d-mesh` | `03_data/D_generated/3d/meshes` |
| `datasets/exports` | `03_data/D_generated/legacy_dataset_exports` |
| `datasets/resources-swirl/results` | `03_data/D_generated/legacy_resources_swirl_results` |
| `generated-figures` | `03_data/D_generated/figures` |
| `KnotPlot/qhp` | `03_data/D_generated/qhp/base` |
| `KnotPlot/qhp_6p3` | `03_data/D_generated/qhp/6p3` |
| `KnotPlot/qhp_extended` | `03_data/D_generated/qhp/extended` |
| `SST_timefield_spectral_v06_research` | `03_data/D_generated/research_outputs/timefield_spectral_v06` |

## E_reference

Namespace reserved: `03_data/E_reference/`. No concrete moves in the current tree.

---

# Soft-delete rule — `DELETE/`

**Nothing is unlinked.** Any path that would previously have been deleted is relocated with
`git mv` to:

```text
DELETE/<original/relative/path/from/repo/root>
```

Examples: `to_be_processed/` → `DELETE/to_be_processed/`;
`experiments/derive_constants/` → `DELETE/experiments/derive_constants/`.
`DELETE/` is gitignored for bulky ignored residue if needed, but tracked stubs stay tracked under
`DELETE/`.

'''

TOTALS = """
# Totals

| Domain-letter | Families |
|---------------|---------:|
| `01_research/A_falsifiers` | 42 |
| `01_research/B_closures` | 5 |
| `01_research/C_dynamics` | 6 |
| `01_research/D_benchmarks` | 9 |
| `01_research/E_pipelines` | 9 |
| `01_research/F_exploratory` | 4 |
| `02_libraries` | 3 |
| `03_data` | provenance dirs (no family IDs) |
| `04_tools` | 6 |
| `05_apps` | 4 |

Research catalog families in 01: **73** canonical from inventory map (A42+B5+C6+D9+E9+F2)
plus F003/F004 residuals kept via git mv (CoilLab, taxonomy). A005 reserved has no move.
"""


def rewrite_catalog() -> None:
    md = CATALOG.read_text(encoding="utf-8")
    # Fix A note about D004/D005 → D006/D007
    md = md.replace(
        "under `D_benchmarks` (D004, D005), not\nhypothesis-bearing A falsifiers.",
        "under `D_benchmarks` (D006, D007), not\nhypothesis-bearing A falsifiers.",
    )
    # Replace from B_closures through end of 03_data (before # 04_tools)
    pattern = re.compile(
        r"## B_closures — closure and field-equation research\n.*?(?=\n# 04_tools)",
        re.S,
    )
    md2, n = pattern.subn(CATALOG_B_THROUGH_03.lstrip() + "\n", md, count=1)
    if n != 1:
        raise SystemExit(f"catalog B..03 replace failed n={n}")
    # Replace totals
    md2 = re.sub(r"# Totals\n.*?(?=\n## Changes since first draft|\Z)", TOTALS + "\n", md2, count=1, flags=re.S)
    # Keep 04_tools and 05_apps and 06-10 — but strip old 02/03 if duplicated
    # Fix QHP generator: was tools A003; now E007 — note in tools section
    md2 = md2.replace(
        "| A003 | `knotplot_qhp_sweep_generator` | SST KnotPlot QHP Sweep Generator | `SST_QHP_Stability_Landscape/SST_KnotPlot_QHP_*` | confirmed |",
        "| A003 | _(moved)_ | QHP Sweep Generator is **E007** under pipelines | — | moved |",
    )
    CATALOG.write_text(md2, encoding="utf-8")
    print("Wrote", CATALOG)


def rewrite_path_map() -> None:
    rows = list(csv.DictReader(PATH_MAP.open(encoding="utf-8")))
    fields = list(rows[0].keys())
    # index overrides
    override = {m[0]: m for m in MOVES}

    out = []
    seen_old = set()
    for row in rows:
        old = row["old_path"]
        seen_old.add(old)
        if old in override:
            _, new, domain, letter, cid, kind, phase = override[old]
            row["new_path"] = new
            row["domain"] = domain
            row["letter"] = letter
            row["catalog_id"] = cid
            row["kind"] = kind
            row["phase"] = phase
            if new.startswith("DELETE/"):
                row["junction"] = "no"
                row["note"] = (row.get("note") or "") + "; soft_delete_via_DELETE/"
            # CoilLab / twin F renumber notes
            if "F003_coil_digital" in new or "F001_coil_digital" in new:
                row["catalog_id"] = "F001"
            if old == "SST_CoilLab_research":
                row["catalog_id"] = "F003"
                row["new_path"] = "01_research/F_exploratory/F003_coil_lab"
                row["letter"] = "F_exploratory"
        else:
            # rewrite known wrong destinations by substring
            np = row["new_path"]
            replacements = [
                ("F_exploratory/F003_coil_digital_twin", "F_exploratory/F001_coil_digital_twin"),
                ("F_exploratory/F002_coil_lab", "F_exploratory/F003_coil_lab"),
                ("F_exploratory/F006_contra_swirl_bridge", "B_closures/B005_contra_swirl_bridge"),
                ("B_closures/B002_route_b_rt_bem", "B_closures/B004_route_b_rt_bem"),
                ("B_closures/B007_ssdl_audit", "D_benchmarks/D004_ssdl_audit"),
                ("B_closures/B005_horn_dirichlet", "B_closures/B003_horn_bem"),
                ("B_closures/B006_horn_neumann", "B_closures/B003_horn_bem"),
                ("D_benchmarks/D001_embedded_knots_verification", "D_benchmarks/D003_verification_suites"),
                ("D_benchmarks/D004_minimal_falsification_harness", "D_benchmarks/D006_minimal_falsification_harness"),
                ("D_benchmarks/D005_sutcliffe_hss_feasibility_gate", "D_benchmarks/D007_sutcliffe_hss_feasibility_gate"),
                ("F_exploratory/F001_fs_attachment_audit", "D_benchmarks/D002_fs_attachment_audit"),
                ("F_exploratory/F005_route_i_relative_entropy", "F_exploratory/F002_route_i_relative_entropy_poc"),
                ("F_exploratory/F008_sycl_probes", "04_tools/D_compute/sycl_probes"),
                ("03_data/A_knots/A006_fremlin_fourier_series", "03_data/A_knots/02_fourier/fremlin_fourier_series"),
                ("03_data/A_knots/A004_ideal_gilbert", "03_data/A_knots/01_ideal/ideal_sources"),
                ("03_data/A_knots/A005_katlas_sources", "03_data/A_knots/03_katlas"),
                ("03_data/C_reference/C001_media", "03_data/C_media"),
                ("03_data/D_generated/D002_figures", "03_data/D_generated/figures"),
                ("03_data/A_knots/A008_parametric_trefoil_seed_atlas", "01_research/E_pipelines/E009_ptsa_parametric_trefoil_seed_atlas"),
                ("03_data/B_external/B001_sparc_and_papers", "03_data/B_external"),  # container; SPARC child separate
                ("02_libraries/A_knot_geometry/A001_knot_geometry_library", "02_libraries/A_knot_libraries/A001_knot_geometry_library"),
                ("02_libraries/C_finite_core/C001_finite_core_spectral_selector", "02_libraries/B_finite_core/B001_independent_finitecore_spectral_selector"),
                ("02_libraries/B_knot_data/B001_knot_library", "02_libraries/A_knot_libraries/A002_knot_library"),
                ("09_archive/pending_delete/", "DELETE/"),
                ("09_archive/relocation_stubs/", "DELETE/"),
            ]
            for a, b in replacements:
                if a in np:
                    np = np.replace(a, b)
            row["new_path"] = np
            # catalog_id from path if research
            m = re.search(r"/(?:A|B|C|D|E|F)(\d{3})_", np)
            # better:
            m2 = re.search(r"/([ABCDEF]\d{3})_", np)
            if m2 and "01_research" in np:
                row["catalog_id"] = m2.group(1)
            if np.startswith("DELETE/"):
                row["domain"] = "DELETE"
                row["junction"] = "no"
                note = row.get("note") or ""
                if "soft_delete" not in note:
                    row["note"] = (note + "; soft_delete_via_DELETE/").lstrip("; ")
        # Never leave action as hard delete in notes
        if row.get("note"):
            row["note"] = row["note"].replace("directory deleted", "directory git_mv to DELETE/")
            row["note"] = re.sub(r"\bdelete\b —", "git_mv to DELETE/ —", row["note"], flags=re.I)
        out.append(row)

    # append missing override rows
    for old, new, domain, letter, cid, kind, phase in MOVES:
        if old in seen_old:
            continue
        out.append(
            {
                "old_path": old,
                "new_path": new,
                "domain": domain,
                "letter": letter,
                "catalog_id": cid,
                "kind": kind,
                "phase": phase,
                "junction": "no" if new.startswith("DELETE/") else "yes",
                "status": "pending",
                "note": "added_by_01_03_freeze" + ("; soft_delete_via_DELETE/" if new.startswith("DELETE/") else ""),
            }
        )

    with PATH_MAP.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out)
    print("path_map rows", len(out))


def rewrite_sp11_and_epic() -> None:
    sp = SP11.read_text(encoding="utf-8")
    sp = sp.replace(
        "The only sub-plan that deletes anything.",
        "The only sub-plan that soft-retires paths. **Nothing is unlinked.**",
    )
    sp = sp.replace(
        "These describe a filesystem that no longer exists. Delete.",
        "These describe a filesystem that no longer exists. "
        "`git mv` each to `DELETE/<original/relative/path>` "
        "(e.g. `to_be_processed/` → `DELETE/to_be_processed/`).",
    )
    sp = sp.replace(
        "Delete after confirming each family's `run_01_install.cmd` can recreate it.",
        "Stage ignored residue under `DELETE/<pack-relative-path>/` after confirming "
        "each family's `run_01_install.cmd` can recreate it — still no `rm -rf` of research trees.",
    )
    sp = sp.replace(
        "C:\\workspace\\projects\\DELETE",
        "`DELETE/<original/relative/path>` under the repo root",
    )
    # section title
    if "Soft-delete via DELETE/" not in sp:
        sp = "## Soft-delete via `DELETE/`\n\n" + (
            "Any former delete candidate is relocated with `git mv` to "
            "`DELETE/<path relative to repo root>`, preserving the original folder layout. "
            "No `git rm`, no filesystem unlink of research or stub content.\n\n"
        ) + sp
    SP11.write_text(sp, encoding="utf-8")
    print("Updated SP11")

    epic = EPIC.read_text(encoding="utf-8")
    if "DELETE/<original" not in epic:
        epic = epic.replace(
            "3. **No deletion outside SP11**, and SP11 only runs after SP10 passes.",
            "3. **No content deletion, ever.** Former delete candidates are `git mv`'d to "
            "`DELETE/<original/relative/path>`. SP11 only runs after SP10 passes and performs "
            "soft-retire + junction cleanup — never `rm` of research trees.",
        )
    EPIC.write_text(epic, encoding="utf-8")
    print("Updated EPIC")

    readme = README.read_text(encoding="utf-8")
    if "DELETE/" not in readme:
        readme = readme.replace(
            "1. **Never delete during a move.** Moves are `git mv` or `robocopy /MOVE`. Deletion happens only\n"
            "   in SP11, only after SP10 has passed.",
            "1. **Never delete content.** Moves are `git mv`. Anything formerly slated for deletion goes to\n"
            "   `DELETE/<original/relative/path>` (still via `git mv`). SP11 soft-retires only after SP10.",
        )
    README.write_text(readme, encoding="utf-8")
    print("Updated README")


def patch_restructure_plan_deletes() -> None:
    text = RESTRUCTURE_PLAN.read_text(encoding="utf-8")
    text = text.replace(
        "delete — one relocation `README.md`, content moved long ago",
        "`git mv` → `DELETE/to_be_processed/` (preserve relative path)",
    )
    text = text.replace(
        "`derive_constants/` and `trefoil/` are stubs, delete",
        "`derive_constants/` and `trefoil/` stubs → `DELETE/experiments/...`",
    )
    text = text.replace(
        "directory deleted. `falsifier_registry.yaml` stays at repo root",
        "README `git mv` → `DELETE/falsifier_registry/`; `falsifier_registry.yaml` stays at repo root",
    )
    # F / data destination fixes in tables (best-effort)
    reps = [
        ("`R/F/F003_coil_digital_twin/`", "`R/F/F001_coil_digital_twin/`"),
        ("`R/F/F002_coil_lab/`", "`R/F/F003_coil_lab/`"),
        ("`R/F/F006_contra_swirl_bridge/`", "`R/B/B005_contra_swirl_bridge/`"),
        ("`R/B/B002_route_b_rt_bem/`", "`R/B/B004_route_b_rt_bem/`"),
        ("`R/D/D001_embedded_knots_verification/`", "`R/D/D003_verification_suites/`"),
        ("`R/D/D004_minimal_falsification_harness/`", "`R/D/D006_minimal_falsification_harness/`"),
        ("`R/D/D005_sutcliffe_hss_feasibility_gate/`", "`R/D/D007_sutcliffe_hss_feasibility_gate/`"),
        ("`D/A/A006_fremlin_fourier_series/`", "`D/A/02_fourier/fremlin_fourier_series/`"),
        ("`D/A/A004_ideal_gilbert/`", "`D/A/01_ideal/ideal_sources/`"),
        ("`D/C/C001_media/`", "`D/C_media/`"),
        ("`D/D/D002_figures/`", "`D/D/figures/`"),
    ]
    for a, b in reps:
        text = text.replace(a, b)
    RESTRUCTURE_PLAN.write_text(text, encoding="utf-8")
    print("Patched RESTRUCTURE_PLAN")


def main() -> None:
    rewrite_catalog()
    rewrite_path_map()
    rewrite_sp11_and_epic()
    patch_restructure_plan_deletes()
    # update freeze plan note
    freeze = PLAN / "CATALOG_01_03_FREEZE.plan.md"
    if freeze.exists():
        t = freeze.read_text(encoding="utf-8")
        t = t.replace("09_archive/", "DELETE/<original/relative/path>/")
        if "DELETE/<original" not in t.split("Harde regel")[1][:500]:
            t = t.replace(
                "**Alles verplaatsen met `git mv`. Niets verwijderen.**",
                "**Alles verplaatsen met `git mv`. Niets verwijderen.** "
                "Former delete candidates → `DELETE/<original/relative/path>`.",
            )
        freeze.write_text(t, encoding="utf-8")


if __name__ == "__main__":
    main()
