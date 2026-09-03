# SST-Workbench CATALOG v0.1

Status: `PLANNED` · Baseline: 2026-09-03

The permanent identity register. A catalog code names a **research family**, not a version and not
a directory. It survives renames, restructures and version bumps. This document outlives the
migration: after SP11 it becomes the place new work registers itself.

## Allocation rule

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
| A001 | `contact_billiard_hydrodynamic` | SST Contact Billiard Hydrodynamic Falsifier | `SST_contact_billiard_hydrodynamic_falsifier/` | 2026-08-01 | confirmed |
| A002 | `dimensionless_dynamic_predictions` | SST Dimensionless Dynamic Predictions | `SST_dimensionless_dynamic_predictions/` | 2026-08-01 | confirmed |
| A003 | `minimal_falsification_harness` | SST Minimal Falsification Harness | `SST_minimal_falsification_harness/` | 2026-08-01 | confirmed |
| A004 | `sutcliffe_hss_feasibility_gate` | SST Sutcliffe HSS Feasibility Gate | `SST_Sutcliffe_HSS_feasibility_gate/` | 2026-08-03 | confirmed |
| A005 | `chiral_kelvin_mode` | SST Chiral Kelvin Mode Falsification | `SST_Chiral-Kelvin-Mode/` | 2026-08-07 | confirmed |
| A006 | `preferred_frame_binary` | SST Preferred Frame Binary Falsifier | `SST_preferred_frame_binary_falsifier/` | 2026-08-07 | confirmed |
| A007 | `counterpulley_alpha` | SST Counterpulley Alpha Falsifier | `SST_counterpulley_alpha_falsifier/` | 2026-08-10 | confirmed |
| A008 | `einstein_blind` | Einstein SST Blind Falsifier | `SST_Einstein/Einstein_SST_Blind_Falsifier_*` | 2026-08-13 | confirmed |
| A009 | `einstein_emergent_metric_poisson_closure` | Einstein SST Emergent Metric Poisson Closure Gates | `SST_Einstein/Einstein_SST_Emergent_Metric_*` | 2026-08-13 | confirmed |
| A010 | `helmholtz_vortex_gates` | Helmholtz SST Vortex Gates Falsifier | `SST_Helmholtz/` | 2026-08-13 | confirmed |
| A011 | `maxwell_kinetic` | Maxwell SST Kinetic Falsifier | `SST_Maxwell/1_Maxwell_SST_Kinetic_*` | 2026-08-13 | confirmed |
| A012 | `maxwell_dynamical_field_closure` | Maxwell SST Dynamical Field Closure Falsifier | `SST_Maxwell/2_Maxwell_SST_Dynamical_*` | 2026-08-13 | confirmed |
| A013 | `maxwell_physical_lines` | Maxwell SST Physical Lines Falsifier | `SST_Maxwell/3_Maxwell_SST_Physical_Lines_*` | 2026-08-13 | confirmed |
| A014 | `maxwell_blind` | SST Maxwell Blind Falsifier | `SST_Maxwell/3_SST_Maxwell_Blind_*` | 2026-08-13 | confirmed |
| A015 | `maxwell_core` | SST Maxwell Falsifier | `SST_Maxwell/4_SST_Maxwell_Falsifier_*` | 2026-08-13 | confirmed |
| A016 | `maxwell_reciprocal` | Maxwell SST Reciprocal Falsifier | `SST_Maxwell/5_*_Reciprocal_*` | 2026-08-13 | confirmed |
| A017 | `kelvin_kirchhoff` | Kelvin Kirchhoff SST Falsifier | `SST_Kelvin_Floquet/Kelvin_Kirchhoff_*` | 2026-08-18 | confirmed |
| A018 | `six_source_blind` | SST 6-Source Blind Falsifier | `SST_6Source_Blind_Falsifier_v0.1.0/` | 2026-08-18 | confirmed |
| A019 | `fourier_vs_ideal` | SST Fourier vs Ideal Blind Falsifier | `SST_Fourier_vs_Ideal_Blind_Falsifier/` | 2026-08-19 | confirmed |
| A020 | `trefoil_lobe_orientation` | SST Trefoil Lobe Orientation Blind Falsifier | `SST_Trefoil_Lobe_Orientation_Blind_Falsifier/SST_Trefoil_Lobe_*` | 2026-08-19 | confirmed |
| A021 | `multitopology_knot_link_tbk_rpo` | SST MultiTopology Knot Link TBK RPO Falsifier | `SST_Trefoil_Lobe_.../SST_MultiTopology_*` | 2026-08-20 | confirmed |
| A022 | `threaded_hole_substrate` | SST Threaded Hole Substrate Blind Falsifier | `SST_Threaded_Hole_..._v0.1.0/SST_Threaded_Hole_*` | 2026-08-20 | confirmed |
| A023 | `local_thread_texture_boost_invariance` | SST Local Thread Texture Boost Invariance Blind Falsifier | `SST_Threaded_Hole_..._v0.1.0/SST_Local_Thread_*` | 2026-08-20 | confirmed |
| A024 | `seven_article_closure_holonomy` | SST 7-Article Closure Holonomy Blind Falsifier | `SST_7Article_Closure_Holonomy/` | 2026-08-21 | confirmed |
| A025 | `finite_core_axial_toroidal_phase_delay` | SST Finite Core Axial Toroidal Phase Delay Blind Falsifier | `SST_Finite_Core_Axial_Toroidal_Phase_Delay/` | 2026-08-21 | confirmed |
| A026 | `phase_feedback_delay_knot_stability` | SST Phase Feedback Delay Knot Stability Blind Falsifier | `SST_Phase_Feedback_Delay_Knot_Stability/` | 2026-08-21 | confirmed |
| A027 | `varrow_spectral` | SST vArrow Spectral Blind Falsifier | `SST_vArrow_Spectral_Blind_Falsifier/` | 2026-08-21 | confirmed |
| A028 | `kelvin_joule_transient_energy` | Kelvin Joule SST Transient Energy Falsifier | `SST_Kelvin_Floquet/Kelvin_Joule_*` | 2026-08-24 | confirmed |
| A029 | `material_phase_eft` | SST Material Phase EFT Falsifier | `SST_Material_Phase_EFT/` | 2026-08-24 | confirmed |
| A030 | `adaptive_period_aware_rpo_floquet` | SST Adaptive Period-Aware RPO Multiple Shooting Floquet Blind Falsifier | `SST_Trefoil_Lobe_.../SST_Adaptive_Period_*` | 2026-08-24 | confirmed |
| A031 | `breathing_stretching_return_phase_causality` | SST Breathing Stretching Return Phase Causality Blind Falsifier | `SST_Breathing_Stretching_Return_Phase_Causality/` | 2026-08-27 | confirmed |
| A032 | `intrinsic_modal_swirl_clock` | SST Intrinsic Modal Swirl Clock Blind Falsifier | `SST_Intrinsic_Modal_Swirl_Clock/SST_Intrinsic_*` | 2026-08-27 | confirmed |
| A033 | `qhp_stability_landscape` | SST QHP Stability Landscape Blind Falsifier | `SST_QHP_Stability_Landscape/SST_QHP_*` | 2026-08-27 | confirmed |
| A034 | `scii_intrinsic_modal_phase_swirl_clock` | SST SCII Intrinsic Modal Phase Swirl Clock Blind Falsifier | `SST_Intrinsic_Modal_Swirl_Clock/SST_SCII_*` | 2026-08-28 | confirmed |
| A035 | `sciib_frozen_modal_pair_subspace_phase_clock` | SST SCIIb Frozen Modal Pair Subspace Phase Clock Blind Falsifier | `SST_Intrinsic_Modal_Swirl_Clock/SST_SCIIb_*` | 2026-08-28 | confirmed |
| A036 | `chirality_helicity_transport_polarity` | SST Chirality Helicity Transport Polarity Falsifier | `SST_Chirality_Helicity_Transport_Polarity/` | 2026-08-28 | confirmed |
| A037 | `trefoil_dynamic_seed_qualification` | SST Trefoil Dynamic Seed Qualification Mega Falsifier | `SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier/` | 2026-08-28 | confirmed |
| A038 | `sciii_koopman_dmd_complex_phase_clock` | SST SCIII Koopman DMD Complex Phase Clock Blind Falsifier | `SST_Intrinsic_Modal_Swirl_Clock/SST_SCIII_*` | 2026-08-30 | confirmed |
| A039 | `quantum_galileo_action_gauge_closure` | SST Quantum Galileo Action Gauge Closure Falsifier | `SST_Quantum_Galileo_Action_Gauge_Closure/` | 2026-09-03 | confirmed |
| A040 | `wien_planck_field_matter_closure` | Wien-Planck SST Field Matter Closure Falsifier | `Wien_Planck_SST_Field_Matter_Closure/` | 2026-09-03 | confirmed |

**Reveal keys are not families.** `3_Maxwell_SST_Physical_Lines_Unblind_Key_v0.2.0`,
`3_SST_Maxwell_Blind_Unblind_Key_v0.1.0` and
`SST_Quantum_Galileo_..._v0.1.1_REVEAL_KEY` are *variants* of a version, and live inside their
family alongside the version they unlock. They never get their own catalog ID. See SP06 §Reveal
keys.

## B_closures — closure and field-equation research

| ID | Family | Official name | Current location | First version | Status |
|----|--------|---------------|------------------|---------------|--------|
| B001 | `derive_constants` | SST Derive Constants Research | `SST_derive_constants_research/` | 2026-06-04 | confirmed |
| B002 | `route_b_rt_bem` | SST Route-B R–T BEM Research | `SST_routeB_RT_bem_research/` | 2026-07-03 | confirmed |
| B003 | `planck_routes_a_to_d_equivalence` | SST v0.8.19 Planck Routes A–D Equivalence | `SST_v0_8_19_routes_research/..._A_to_D_*` | 2026-07-06 | confirmed |
| B004 | `planck_routes_v3_preregistered` | SST v0.8.19 Planck Routes v3 Preregistered | `SST_v0_8_19_routes_research/..._v3_prereg*` | 2026-07-06 | confirmed |
| B005 | `route_a_parallel_derivation` | SST v0.8.19 Route-A Parallel Derivation Falsification | `SST_v0_8_19_routes_research/..._RouteA_*` | 2026-07-06 | confirmed |
| B006 | `horn_dirichlet_bem` | SST Horn-Torus Dirichlet BEM | `SST_horn_bem_research/sst_horn_dirichlet_*` | 2026-07-07 | confirmed |
| B007 | `horn_neumann_bem` | SST Horn-Torus Neumann BEM | `SST_horn_bem_research/sst_horn_neumann_*` | 2026-07-08 | confirmed |
| B008 | `ssdl_audit` | SST Separatrix Surface-Density Lift Audit | `SST_ssdl_audit_research/` | 2026-07-08 | confirmed |

## C_dynamics — vortex, finite-core and Floquet dynamics

| ID | Family | Official name | Current location | First version | Status |
|----|--------|---------------|------------------|---------------|--------|
| C001 | `chi_phase_track_b` | SST Chi-Phase Track B | `SST_Trefoil_Closure/sst_chi_phase_package*` + `SST_chi_phase_research/sst_chi_phase_package_v1*B*` | 2026-07-03 | confirmed |
| C002 | `chi_e_biot_savart` | SSTcore ChiE Local Biot–Savart | `SST_chi_phase_research/sstcore_chiE_local*` | 2026-07-06 | confirmed |
| C003 | `ideal_trefoil_biot` | SST Ideal Trefoil Biot–Savart | `SST_ideal_trefoil_biot_research/sst_ideal_trefoil_biot_package_v2` | 2026-07-06 | confirmed |
| C004 | `torsion_impedance` | SST Torsion Impedance pybind11 | `SST_v0_8_19_routes_research/sst_torsion_impedance_*` | 2026-07-07 | confirmed |
| C005 | `3d_collider` | SST 3D Collider Robust | `SST_ideal_trefoil_biot_research/sst_3d_collider_robust` | 2026-07-08 | confirmed |
| C006 | `uq_twisted_vortex_ring` | U(q) Twisted Vortex Ring Speed Deficit Experiment | `GUI/additional for Vlab/` | 2026-07-25 | confirmed |
| C007 | `fermat_biot_savart` | SST Fermat-Metric / Biot–Savart Knot Diagnostics | `SST_fermat_pybind_research/` | 2026-07-28 | confirmed |
| C008 | `kelvin_floquet_workbench` | SST Kelvin Floquet Workbench (C++/pybind) | `SST_Kelvin_Floquet/SST_Kelvin_Floquet_Workbench_*` | 2026-08-10 | confirmed |

**C001 spans two current roots.** The early `sst_chi_phase_package` v1–v6 under `SST_Trefoil_Closure/`
is the direct ancestor of the `v10B1`–`v16B0` Track B series. One family, one continuous lineage.

**C006 is not a GUI asset.** `GUI/additional for Vlab/` is a self-contained physics experiment: an
axisymmetric Euler solver on a 256x512 grid measuring the ring-speed deficit of a twisted vortex
ring, to fix the Kirchhoff twist-stiffness prefactor `C_eff` and discriminate a Rankine core from a
hollow core. Its README records the status upgrade "derived to numerically verified". It lives
under `GUI/` only because it carries port notes for the VortexLab simulator.

**`sst_trefoil_bs` is not here.** It is a numerics kernel, not a research family — see
`02_libraries/D_numerics/D001`.

## D_benchmarks — numerical verification and benchmarks

| ID | Family | Official name | Current location | First version | Status |
|----|--------|---------------|------------------|---------------|--------|
| D001 | `embedded_knots_verification` | Embedded Knots Verification Suite | `verification-suites/embedded-knots/` | 2026-07-03 | confirmed |
| D002 | `hopf_benchmark_packet` | SST Hopf Benchmark Packet | `SST_Hopf_Benchmark/SST_Hopf_Benchmark_Packet_*` | 2026-08-01 | confirmed |
| D003 | `ideal_links_test_suite` | SST Ideal Links Comprehensive Test Suite | `SST_ideal_links/` | 2026-08-04 | confirmed |
| D004 | `hopf_cpp_pybind` | SST Hopf Charge / Spin-Route Gate (C++/pybind) | `SST_Hopf_Benchmark/SST_Hopf_cpp_pybind_*` | 2026-08-07 | confirmed |

## E_pipelines — dataset, knot and processing pipelines

| ID | Family | Official name | Current location | First version | Status |
|----|--------|---------------|------------------|---------------|--------|
| E001 | `sst21d_knot_order` | SST-21D Knot Order Pipeline | `SST21D_knot_order_pipeline/` | 2026-08-01 | confirmed |
| E002 | `trefoil_balance_tbk_rpo_handoff` | Trefoil Balance to TBK RPO Handoff | `Trefoil_Balance_to_TBK_RPO_Handoff_v0.1.0/` | 2026-08-24 | confirmed |
| E003 | `katlas_link_geometry_conditioning` | SST Katlas Link Geometry Conditioning | `SST_Katlas_Link_Geometry_Conditioning_v2.0.0/` | 2026-08-30 | confirmed |
| E004 | `knotplot_trefoil_balance_point` | KnotPlot Trefoil Balance Point Campaign | `KnotPlot/Trefoil_Balance_Point_Campaign_*` | TBC | provisional |
| E005 | `knotplot_trefoil_seed` | KnotPlot 3p1 Trefoil Seed Campaign | `KnotPlot/KnotPlot_3p1_Trefoil_Seed_Campaign_*` | TBC | provisional |
| E006 | `knotplot_multidynamics_relaxation_matrix` | KnotPlot 3p1 MultiDynamics Relaxation Matrix | `KnotPlot/KnotPlot_3p1_MultiDynamics_*` | TBC | provisional |
| E007 | `knotplot_dynamics_parameter_atlas` | KnotPlot 3p1 Comprehensive Dynamics Parameter Atlas | `KnotPlot/KnotPlot_3p1_Comprehensive_*` | TBC | provisional |
| E008 | `knotplot_command_certification` | KnotPlot 3p1 MissingParameter Command Certification | `KnotPlot/KnotPlot_3p1_MissingParameter_*` | TBC | provisional |
| E009 | `knotplot_multitopology_qhp_sweep` | KnotPlot MultiTopology QHP Sweep | `KnotPlot/KnotPlot_MultiTopology_QHP_Sweep_*` | TBC | provisional |

E004–E009 dates are confirmed in SP07, which owns the KnotPlot split.

## F_exploratory — PoCs and not-yet-formalized research

| ID | Family | Official name | Current location | First version | Status |
|----|--------|---------------|------------------|---------------|--------|
| F001 | `fs_attachment_audit` | SST Framed-Helicity / Attachment Audit | `SST_fs_attachment_audit_research/` | 2026-06-25 | confirmed |
| F002 | `coil_lab` | SST CoilLab | `SST_CoilLab_research/` | 2026-06-26 | confirmed |
| F003 | `coil_digital_twin` | SST Coil Digital Twin | `SST_Coil_DigitalTwin_research/` | 2026-06-26 | confirmed |
| F004 | `route_i_heat_guard_patch` | Route-I Heat Guard Patch Bundle | `SST_Route_I_relative_entropy_PoC/routeI_heat_guard_*` | 2026-07-06 | confirmed |
| F005 | `nonfit_prediction_harness` | SST Non-Fit Prediction Harness | `SST_v0_8_19_routes_research/sst_nonfit_*` | 2026-07-07 | confirmed |
| F006 | `dark_knot_rayleigh` | SST Dark-Knot Rayleigh / Rocking Audit | `SST_dark_knot_rayleigh_research/` | 2026-07-08 | confirmed |
| F007 | `route_i_relative_entropy` | SST Route-I Relative Entropy PoC | `SST_Route_I_relative_entropy_PoC/SST_Route_I_*` | 2026-07-28 | confirmed |
| F008 | `contra_swirl_bridge` | SST Contra-Swirl Bridge | `SST_contra_swirl_bridge_research/` | 2026-08-01 | confirmed |
| F009 | `taxonomy_starter` | SST Taxonomy Starter | `SST_Trefoil_Closure/sst_taxonomy_starter_*` | 2026-08-01 | provisional |
| F010 | `sycl_probes` | SYCL Device Probes | `experiments/sycl/` | TBC | provisional |

The early `sst_chi_phase_package` v1–v6 under `SST_Trefoil_Closure/` is **not** an exploratory
family. It is the ancestor of the Track B series and folds into `C001_chi_phase_track_b`.

---

# 02_libraries

| ID | Family | Official name | Current location | First version | Status |
|----|--------|---------------|------------------|---------------|--------|
| A001 | `knot_geometry_library` | SST Knot Geometry Library | `Knot_Geometry_Library/` | 2026-08-29 | confirmed |
| B001 | `knot_library` | SST Knot Library | `Knot_Library/SST_Knot_Library/` | 2026-08-30 | confirmed |
| C001 | `finite_core_spectral_selector` | Independent Finite-Core Spectral Selector | `Independent_FiniteCore_SpectralSelector/` | 2026-08-07 | confirmed |
| D001 | `trefoil_biot_savart_kernel` | SST Trefoil Biot–Savart Kernel | `SST_ideal_trefoil_biot_research/sst_trefoil_bs/` | 2026-07-11 | confirmed |

**D001 is a kernel, not a research family.** `sst_trefoil_bs/` holds `sst_bs_kernel.cpp`, a
`build.py`, an `ideal_source.py` loader and a `trefoil_energy.py` pipeline. Nothing imports it as a
package, and it produces no falsification gate — it is reusable numerics that ended up filed as
research.

**Open finding: `sst_trefoil_biot_py` exists six times.** Identical-by-name copies live in
`SST_chi_phase_research/sstcore_chiE_local{0,_v4,_v5,_v6,_v7}/` and
`SST_ideal_trefoil_biot_research/sst_ideal_trefoil_biot_package_v2/`, alongside six copies of
`sst_trefoil_biot_build.py`. It is imported by at least eight files across two families. This is the
strongest candidate for a second `D_numerics` entry.

Deduplicating it is **not** part of the migration. Each version pinned its own copy, and collapsing
them would change what those versions compute. The correct handling, recorded in SP06: promote the
newest copy to `D_numerics/D002_trefoil_biot_py/` for new work, leave every version's copy in place,
and diff the six to record whether they have actually diverged.

---

# 03_data

## A_knots — knot geometry datasets

| ID | Dataset | Current location | Approx. size | Status |
|----|---------|------------------|--------------|--------|
| A001 | `knotplot_relaxed` | `KnotPlot/knots/` | ~7.8 GB | confirmed |
| A002 | `knotplot_fourier_series` | `KnotPlot/Knots_FourierSeries/` | ~0.7 MB | confirmed |
| A003 | `knotplot_qhp` | `KnotPlot/qhp/`, `qhp_6p3/`, `qhp_extended/` | ~29 MB | confirmed |
| A004 | `ideal_gilbert` | `Ideal_Sources/` | — | confirmed |
| A005 | `katlas_sources` | `Katlas_Sources_v0.2.2_Outputs/` | — | confirmed |
| A006 | `fremlin_fourier_series` | `Fremlin_FourierSeries/` | — | confirmed |
| A007 | `knot_library_sources` | `Knot_Library/{Sources,Derived,Registry,Quarantine}/` | — | confirmed |
| A008 | `parametric_trefoil_seed_atlas` | `PTSA_Parametric_Trefoil_Seed_Atlas_v1.0.0/` | — | confirmed |

## B_external — third-party datasets

| ID | Dataset | Current location | Status |
|----|---------|------------------|--------|
| B001 | `sparc_and_papers` | `datasets/` | confirmed |

## C_reference — reference assets

| ID | Asset set | Current location | Approx. size | Status |
|----|-----------|------------------|--------------|--------|
| C001 | `media` | `media/` | ~1.46 GB | confirmed |
| C002 | `gui_images` | `GUI/images/` | — | confirmed |

## D_generated — generated results

| ID | Result set | Current location | Approx. size | Status |
|----|------------|------------------|--------------|--------|
| D001 | `3d_exports` | `3D/**/*.stl`, `3D/Python/3d_sliced/*.gcode` | ~2.5 GB | confirmed |
| D002 | `figures` | `generated-figures/` | ~13 MB | confirmed |
| D003 | `timefield_spectral` | `SST_timefield_spectral_v06_research/` | ~27 MB | confirmed |
| D004 | `routeb_shared_outputs` | `SST_routeB_RT_bem_research/outputs/`, `shared/` | — | confirmed |
| D005 | `knotplot_campaign_outputs` | `KnotPlot/ridgerunner/out/` | ~3.9 GB | confirmed |

---

# 04_tools

| ID | Tool | Official name | Current location | Status |
|----|------|---------------|------------------|--------|
| A001 | `knotplot` | KnotPlot driver scripts and `.kps` configs | `KnotPlot/*.py`, `*.kps`, `KnotPlot.lnk` | confirmed |
| A002 | `ridgerunner` | RidgeRunner ladder scripts and binaries | `KnotPlot/ridgerunner/` (excl. `out/`) | confirmed |
| A003 | `knotplot_qhp_sweep_generator` | SST KnotPlot QHP Sweep Generator | `SST_QHP_Stability_Landscape/SST_KnotPlot_QHP_*` | confirmed |
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
| `01_research/A_falsifiers` | 40 |
| `01_research/B_closures` | 8 |
| `01_research/C_dynamics` | 8 |
| `01_research/D_benchmarks` | 4 |
| `01_research/E_pipelines` | 9 |
| `01_research/F_exploratory` | 10 |
| `02_libraries` | 4 |
| `03_data` | 16 |
| `04_tools` | 6 |
| `05_apps` | 4 |
| **Total** | **109** |

109 catalog entries from 73 current roots: the container splits create 36 net new identities that
previously had no independent existence in the filesystem.

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
