# SST-Workbench CATALOG v0.1

Status: `PLANNED` · Baseline: 2026-09-03

The permanent identity register. A catalog code names a **research family**, not a version and not
a directory. It survives renames, restructures and version bumps. This document outlives the
migration: after SP11 it becomes the place new work registers itself.

## Allocation rule

**A-falsifier chronology frozen 2026-09-04** to A001–A042 (earliest created timestamp; A005 reserved for archive-only `finite_core_c2`). This supersedes the interim A001=`contact_billiard` numbering.


IDs are allocated chronologically within each domain-letter, ordered by the **earliest `created`
timestamp among the family's own version directories** — not the root directory, which is often
younger because of earlier reorganisations. `SST_derive_constants_research/` for example has a
root created 2026-08-01 but contents from 2026-06-04; the contents date wins.

New families take the next free number in their domain-letter. **IDs are permanent and are never
reused**, including for families that are later archived or abandoned.

## Confidence

- `confirmed` — the family boundary was verified by directory inspection.
- `provisional` — the boundary is proposed from naming and needs a semantic check before the move.
  Every `provisional` entry is resolved in SP06 or SP07 before it is acted on.

Provisional entries may be renumbered before first use. Confirmed entries may not.

---

# 01_research

## A_falsifiers — formal SST falsifiers and gates

| ID | Family | Official name | Current location | First version | Status |
|----|--------|---------------|------------------|---------------|--------|
| A001 | `route_a_parallel_derivation_falsification` | SST v0.8.19 Route-A Parallel Derivation Falsification | `SST_v0_8_19_routes_research/..._RouteA_*` | 2026-07-06 | confirmed |
| A002 | `nonfit_prediction_routes_control` | SST Non-Fit Prediction Harness (routes control) | `SST_v0_8_19_routes_research/sst_nonfit_*` | 2026-07-07 | confirmed |
| A003 | `dark_knot_rayleigh` | SST Dark-Knot Rayleigh / Rocking Audit | `SST_dark_knot_rayleigh_research/` | 2026-07-08 | confirmed |
| A004 | `dimensionless_dynamic_predictions` | SST Dimensionless Dynamic Predictions | `SST_dimensionless_dynamic_predictions/` | 2026-08-01 | confirmed |
| A005 | `finite_core_c2` | Finite-Core c2 Archive-Only Falsifier (reserved) | `(archive-only; no working-tree package)` | 2026-08-01 | reserved |
| A006 | `contact_billiard_hydrodynamic` | SST Contact Billiard Hydrodynamic Falsifier | `SST_contact_billiard_hydrodynamic_falsifier/` | 2026-08-01 | confirmed |
| A007 | `ideal_links_topology_robustness` | SST Ideal Links Comprehensive Test Suite | `SST_ideal_links/` | 2026-08-04 | confirmed |
| A008 | `chiral_kelvin_core` | SST Chiral Kelvin Mode Falsification | `SST_Chiral-Kelvin-Mode/` | 2026-08-07 | confirmed |
| A009 | `preferred_frame_binary` | SST Preferred Frame Binary Falsifier | `SST_preferred_frame_binary_falsifier/` | 2026-08-07 | confirmed |
| A010 | `counterpulley_alpha_ropelength` | SST Counterpulley Alpha Falsifier | `SST_counterpulley_alpha_falsifier/` | 2026-08-10 | confirmed |
| A011 | `maxwell_1_kinetic_energy` | Maxwell SST Kinetic Falsifier | `SST_Maxwell/1_Maxwell_SST_Kinetic_*` | 2026-08-13 | confirmed |
| A012 | `maxwell_3_physical_lines` | Maxwell SST Physical Lines / Blind Falsifier | `SST_Maxwell/3_Maxwell_SST_Physical_Lines_*` + `SST_Maxwell/3_SST_Maxwell_Blind_*` | 2026-08-13 | confirmed |
| A013 | `maxwell_4_field_null` | SST Maxwell Falsifier (field null) | `SST_Maxwell/4_SST_Maxwell_Falsifier_*` | 2026-08-13 | confirmed |
| A014 | `maxwell_5_reciprocal_figures` | Maxwell SST Reciprocal Falsifier | `SST_Maxwell/5_*_Reciprocal_*` | 2026-08-13 | confirmed |
| A015 | `maxwell_2_dynamical_field` | Maxwell SST Dynamical Field Closure Falsifier | `SST_Maxwell/2_Maxwell_SST_Dynamical_*` | 2026-08-13 | confirmed |
| A016 | `helmholtz_vortex_transport` | Helmholtz SST Vortex Gates Falsifier | `SST_Helmholtz/` | 2026-08-13 | confirmed |
| A017 | `einstein_emergent_metric_poisson` | Einstein SST Emergent Metric Poisson Closure Gates | `SST_Einstein/Einstein_SST_Emergent_Metric_*` | 2026-08-13 | confirmed |
| A018 | `einstein_blind` | Einstein SST Blind Falsifier | `SST_Einstein/Einstein_SST_Blind_Falsifier_*` | 2026-08-13 | confirmed |
| A019 | `kelvin_kirchhoff_evanescent_core` | Kelvin Kirchhoff SST Falsifier | `SST_Kelvin_Floquet/Kelvin_Kirchhoff_*` | 2026-08-18 | confirmed |
| A020 | `six_source_blind_energy` | SST 6-Source Blind Falsifier | `SST_6Source_Blind_Falsifier_v0.1.0/` | 2026-08-18 | confirmed |
| A021 | `trefoil_lobe_self_confinement` | SST Trefoil Lobe Orientation Blind Falsifier | `SST_Trefoil_Lobe_Orientation_Blind_Falsifier/SST_Trefoil_Lobe_*` | 2026-08-19 | confirmed |
| A022 | `fourier_vs_ideal` | SST Fourier vs Ideal Blind Falsifier | `SST_Fourier_vs_Ideal_Blind_Falsifier/` | 2026-08-19 | confirmed |
| A023 | `multitopology_rpo_floquet` | SST MultiTopology Knot Link TBK RPO Falsifier | `SST_Trefoil_Lobe_.../SST_MultiTopology_*` | 2026-08-20 | confirmed |
| A024 | `threaded_hole_separatrix` | SST Threaded Hole Substrate Blind Falsifier | `SST_Threaded_Hole_..._v0.1.0/SST_Threaded_Hole_*` | 2026-08-20 | confirmed |
| A025 | `local_thread_texture_boost` | SST Local Thread Texture Boost Invariance Blind Falsifier | `SST_Threaded_Hole_..._v0.1.0/SST_Local_Thread_*` | 2026-08-20 | confirmed |
| A026 | `phase_feedback_delay_knot_stability` | SST Phase Feedback Delay Knot Stability Blind Falsifier | `SST_Phase_Feedback_Delay_Knot_Stability/` | 2026-08-21 | confirmed |
| A027 | `spectral_swirl_clock` | SST vArrow Spectral Blind Falsifier | `SST_vArrow_Spectral_Blind_Falsifier/` | 2026-08-21 | confirmed |
| A028 | `seven_article_closure_holonomy` | SST 7-Article Closure Holonomy Blind Falsifier | `SST_7Article_Closure_Holonomy/` | 2026-08-21 | confirmed |
| A029 | `finite_core_axial_toroidal_phase_delay` | SST Finite Core Axial Toroidal Phase Delay Blind Falsifier | `SST_Finite_Core_Axial_Toroidal_Phase_Delay/` | 2026-08-21 | confirmed |
| A030 | `material_phase_eft_holonomy` | SST Material Phase EFT Falsifier | `SST_Material_Phase_EFT/` | 2026-08-24 | confirmed |
| A031 | `adaptive_period_rpo_floquet` | SST Adaptive Period-Aware RPO Multiple Shooting Floquet Blind Falsifier | `SST_Trefoil_Lobe_.../SST_Adaptive_Period_*` | 2026-08-24 | confirmed |
| A032 | `kelvin_joule_transient_energy` | Kelvin Joule SST Transient Energy Falsifier | `SST_Kelvin_Floquet/Kelvin_Joule_*` | 2026-08-24 | confirmed |
| A033 | `breathing_stretching_return_phase` | SST Breathing Stretching Return Phase Causality Blind Falsifier | `SST_Breathing_Stretching_Return_Phase_Causality/` | 2026-08-27 | confirmed |
| A034 | `qhp_stability_landscape` | SST QHP Stability Landscape Blind Falsifier | `SST_QHP_Stability_Landscape/SST_QHP_*` | 2026-08-27 | confirmed |
| A035 | `intrinsic_modal_swirl_clock` | SST Intrinsic Modal Swirl Clock Blind Falsifier | `SST_Intrinsic_Modal_Swirl_Clock/SST_Intrinsic_*` | 2026-08-27 | confirmed |
| A036 | `scii_intrinsic_modal_phase_clock` | SST SCII Intrinsic Modal Phase Swirl Clock Blind Falsifier | `SST_Intrinsic_Modal_Swirl_Clock/SST_SCII_*` | 2026-08-28 | confirmed |
| A037 | `chirality_helicity_transport_polarity` | SST Chirality Helicity Transport Polarity Falsifier | `SST_Chirality_Helicity_Transport_Polarity/` | 2026-08-28 | confirmed |
| A038 | `trefoil_dynamic_seed_qualification` | SST Trefoil Dynamic Seed Qualification Mega Falsifier | `SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier/` | 2026-08-28 | confirmed |
| A039 | `sciib_frozen_modal_pair_phase_clock` | SST SCIIb Frozen Modal Pair Subspace Phase Clock Blind Falsifier | `SST_Intrinsic_Modal_Swirl_Clock/SST_SCIIb_*` | 2026-08-28 | confirmed |
| A040 | `sciii_koopman_dmd_phase_clock` | SST SCIII Koopman DMD Complex Phase Clock Blind Falsifier | `SST_Intrinsic_Modal_Swirl_Clock/SST_SCIII_*` | 2026-08-30 | confirmed |
| A041 | `wien_planck_field_matter_closure` | Wien-Planck SST Field Matter Closure Falsifier | `Wien_Planck_SST_Field_Matter_Closure/` | 2026-09-03 | confirmed |
| A042 | `quantum_galileo_action_gauge_closure` | SST Quantum Galileo Action Gauge Closure Falsifier | `SST_Quantum_Galileo_Action_Gauge_Closure/` | 2026-09-03 | confirmed |

**A005 is reserved.** `finite_core_c2` is an archive-only falsifier with no working-tree
package in the current inventory; no filesystem move is generated for it.

**A012 holds both Maxwell `3_` packs.** `3_Maxwell_SST_Physical_Lines_*` and
`3_SST_Maxwell_Blind_*` (plus their unblind keys as variants) share one catalog identity.

**Reveal keys are not families.** Maxwell and Galileo reveal/unblind keys are *variants* of a
version and live inside their family. They never get their own catalog ID. See SP06 §Reveal keys.

**Moved out of A in this chronology.** `SST_minimal_falsification_harness` and
`SST_Sutcliffe_HSS_feasibility_gate` are metrology/gates under `D_benchmarks` (D006, D007), not
hypothesis-bearing A falsifiers. `route_a`, `nonfit`, `dark_knot_rayleigh` and `ideal_links`
moved *into* A (A001–A003, A007).


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
| C007 | `uq_twisted_vortex_ring` | U(q) Twisted Vortex Ring Speed Deficit Experiment | `GUI/additional for Vlab/` | 2026-07-25 | confirmed |

**C007 was added after the freeze.** `GUI/additional for Vlab/` is not an app asset: it
is a self-contained physics experiment that integrates the axisymmetric Euler equations
with swirl on a 256x512 grid to fix the Kirchhoff twist-stiffness prefactor `C_eff` and
tell a Rankine core from a hollow one. The frozen tables classified `GUI/` as apps, so
it never surfaced there. It briefly occupied C006, which belongs to
`kelvin_floquet_workbench`, and moved to the next free number.

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



# 04_tools

| ID | Tool | Official name | Current location | Status |
|----|------|---------------|------------------|--------|
| A001 | `knotplot` | KnotPlot driver scripts and `.kps` configs | `KnotPlot/*.py`, `*.kps`, `KnotPlot.lnk` | confirmed |
| A002 | `ridgerunner` | RidgeRunner ladder scripts and binaries | `KnotPlot/ridgerunner/` (excl. `out/`) | confirmed |
| A003 | _(moved)_ | QHP Sweep Generator is **E007** under pipelines | — | moved |
| B001 | `katlas_source_crawler` | Katlas Source Crawler | `Katlas_Source_Crawler_v0.2.2/` | confirmed |
| C001 | `3d_models` | Coil / gear / mold STL generators | `3D/` (source only) | confirmed |
| D001 | `proof_scripts` | SSTcore examples and swirl proof/simulator trees | `proof-scripts/` | confirmed |

---

# 05_apps

Flat domain. The `A` is a fixed placeholder so the ID format stays uniform; there is no letter
taxonomy here.

| ID | App | Official name | Current location | First version | Status |
|----|-----|---------------|------------------|---------------|--------|
| A001 | `dashboard` | SST Research Dashboard (PyQt5) | `SST-dashboard/` | 2026-07-03 | confirmed |
| A002 | `coil_gui` | Coil GUIs | `GUI/coils/` | 2026-07-05 | confirmed |
| A003 | `vortexlab` | VortexLab | `GUI/vortexring-lab/` + `GUI/vortexlab-modular-v7.6.25b-m1/` | 2026-07-11 | confirmed |
| A004 | `math_lab` | SST Math Lab | `GUI/SST_Math_Lab_v0.2.0/` | 2026-08-27 | confirmed |

**A003 has two lines, and `latest` is not obvious.** `vortexlab-modular-v7.6.25b-m1/` is the
modular rewrite that supersedes the monolith architecturally: a proper monorepo with `apps/web`,
`packages/contracts` and `packages/sstcore-adapter`. But it contains **zero** `.glsl` files against
13 in `vortexring-lab/shaders/`, and its newest file dates from 2026-08-13 while the monolith was
modified 2026-09-03.

The rendering layer has not been ported and active work continues in the monolith. `FAMILY.yaml`
therefore records the modular line as `successor: in-progress`, not as `latest`. Setting `latest` to
the modular line would point every consumer at a build with no shaders.

---

# 06–10: infrastructure domains

No catalog IDs. Descriptive names only.

| Domain | Contents |
|--------|----------|
| `06_templates/` | `SST_cpp_pybind_audit_template/`, `SST_GPU_SYCL_DPC_audit_template/` |
| `07_scripts/` | Repo tooling from `scripts/`, plus the migration tooling built in SP00–SP02 |
| `08_third_party/` | `knot_theory/` (Bar-Natan HFK-Zurich, JavaKh, KnotAtlas, WikiLink, QuantumGroups) |
| `09_archive/` | `restore/` (607 zips, 29 themed buckets), `bundles/` |
| `10_docs/` | `inventory/`, `architecture/`, `migration/`, `registry/` |

---


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


## Changes since first draft

Four entries were marked `provisional` in the first draft and have since been resolved by
inspection. All four moved something.

| Was | Now | Evidence |
|-----|-----|----------|
| `C006_trefoil_biot_savart` (research family) | `02_libraries/D_numerics/D001` | No importers, no gate; a C++ kernel plus builder |
| `F004_trefoil_closure_chi_phase_legacy` (own family) | folded into `C001_chi_phase_track_b` | Continuous lineage v1–v6 to v10B1–v16B0 |
| `A004_vortexlab_modular` (own app) | folded into `A003_vortexlab` | Modular rewrite of the same app, not a second app |
| `GUI/additional for Vlab/` (app assets) | `C006_uq_twisted_vortex_ring` | Standalone axisymmetric Euler experiment with its own results table |

Because no ID had been issued yet, `C_dynamics`, `F_exploratory` and `05_apps` were renumbered to
stay contiguous. **This is the last time renumbering is permitted.** From the moment this catalog is
committed, IDs are fixed and gaps are left where families are retired.
