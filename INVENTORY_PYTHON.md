# SST-Workbench — research Python inventory

Companion to [INVENTORY.md](INVENTORY.md). Focus: **calculation / research scripts**.
Paths are relative to the Workbench root. “Live” means the newest apparently-active
version on disk (highest semver / newest README / richest campaign outputs).

Totals: **1528** `.py` files outside `.venv` / caches; **108** `test_*.py`.

---

## 1. Fermat / geodesic

### `SST_fermat_pybind_research/` (706.7 MB)

Standalone Python + C++17/pybind11 harness for SST Fermat-metric / Biot–Savart knot
diagnostics. Does **not** import SSTcore.

| Versions on disk | Live |
|------------------|------|
| `v0.1`, `v0.2.0`, `v0.3.0`, `v0.4.0`–`v0.4.3`, `v0.4.3_flat`, `v0.5.0`, `v0.5.1`, `v0.6.0`, **`v0.6.1`** | **v0.6.1** — highest semver, 30 `run_*.py`, `BUILD_VALIDATION.txt` 2026-08-01, full-range hole-bundle grid |

Capability timeline: radial profiles (v0.1) → four ideal knots (v0.2) → softening matrices (v0.3) → stationary-root certification (v0.4.x) → 3-D geodesic / monodromy (v0.5.x) → hole-bundle sweep (v0.6.0) → full-range absolute metric (v0.6.1).

**Live entry points (`…_v0.6.1/`):**

| Script | Computes |
|--------|----------|
| `run_v061_campaign.py` | 4-stage hole-bundle campaign (sweep → convergence → axis → mode projection) + ZIP |
| `run_hole_bundle_sweep.py` | Full-range coaxial hole-bundle residual sweep (2730 combos) |
| `run_v061_selected_convergence.py` | Selected-candidate centerline convergence audit |
| `run_v061_axis_audit.py` | Axis-offset / tilt robustness |
| `run_v061_mode_projection.py` | Fourier diagnostic of residual modes reduced by the bundle |
| `run_geodesic_shooting.py` | Shoot 3-D Fermat rays from local-minimum seeds |
| `run_orbit_convergence.py` | Two-axis global closed-orbit convergence gate |
| `run_monodromy.py` / `run_monodromy_smoke.py` | Reduced monodromy scan / smoke |
| `run_candidate_atlas.py` | Radial Fermat stationary roots for four-knot matrix |
| `run_bifurcation_atlas.py` | Candidate branches vs softening |
| `run_all_checks.py` | Native/Python parity audit battery |
| (+ retained v0.4–v0.5 `run_*.py`) | Profile / knot / softening / campaign legacy runners |

**Native extension:** `fermat_ext._fermat_native` via `fermat_ext/build_ext_if_needed.py`
(`cpp/native.cpp`). Python fallback in `fermat_ext/fallback.py`.

**Tests:** `tests/test_v061.py` (+ versioned predecessors); standalone scripts, **no pytest.ini**.
**Outputs:** `v0.6.1_*_output/` plus leftover `v0.6.0_*_output/` dirs inside the live tree.

`v0.4.3_flat` = identical source to `v0.4.3` without build/campaign artifacts.

---

## 2. BEM / spectral

### `SST_routeB_RT_bem_research/` (154.3 MB)

Route-B R–T spectral / BEM falsifier chain on knot-tube geometry.

| Versions | Live |
|----------|------|
| `stecklov`, `v3`, `v3_1`–`v3_3`, `v4`…`v19` | **v18** for production BEM scans; **v19** newest code (link geometry parser, no final BEM yet). Shared gate workspace: `outputs/` |

Progression: geometry loaders (v3.x) → spectral action + normalizers (v4–v9) → certified length (v10–v13) → multigrid (v14–v15) → heat-kernel proof obligations (v16–v17) → multi-knot empirical tests (v18) → link parser (v19).

**Version-line entry points (one falsifier per folder):**

| Script | Computes |
|--------|----------|
| `…_stecklov/routeB_RT_bem_stecklov_falsifier.py` | 3D knot-tube complement BEM/Steklov R–T falsifier |
| `…_v3/routeB_RT_bem_v3_falsifier.py` | Tube-BEM with Bishop frames |
| `…_v3_1/…_sstcore_falsifier.py` | Geometry from SSTcore / ideal.txt |
| `…_v3_2/…_idealxml_falsifier.py` | Brian Gilbert ideal.txt XML/Fourier loader |
| `…_v3_3/…_idealxml_falsifier.py` | Refined ideal.txt compatibility |
| `…_v4/…_zeta_falsifier.py` | Spectra, mode-cutoff, renormalized-action fit, blind α |
| `…_v5/…_soft_hk_falsifier.py` | Soft-sector + heat-kernel counterterms |
| `…_v6/…_convergence_grid.py` | Mesh/tube/boundary convergence grid |
| `…_v7/…_spectral_length_budget.py` | Spectral-length + finite R–T budget |
| `…_v8/…_pair_length_budget.py` | Fourier arclength + pair-subtracted correction |
| `…_v9/…_correction_normalizer.py` | α-blind N_q normalizer scan |
| `…_v10`–`v13` | Normalizer convergence, length provenance, Fourier convention, certified budget |
| `…_v14/…_certified_convergence.py` + `…_multirun_grids.py` | Certified-length mesh grid + multi-family launcher |
| `…_v15/…_normalizer_law.py` | Empirical N_RT = M_max L_cert² |
| `…_v16`–`v17` | Heat-kernel / principal-symbol normalizer derivation |
| `…_v18/…_multiknot_exponent_test.py` + extended scans | Multi-knot ΔF_pair exponent tests (KnotPlot IDs) |
| `…_v19/…_link_geometry_parser.py` | Multi-component link geometry (L2a1, …) |

**Shared:** `shared/bem_scale_roles.py`; `knot-data/knotplot/knot_batch_v2.py` / `v3.py`,
`sst_helicity_balance_scan.py`, `raw_2_fseries.py`, etc.

**`outputs/`:** ~28 gate-auditor scripts that **mirror**
`SST_derive_constants_research/code/` (see [INVENTORY_DUPLICATES.md](INVENTORY_DUPLICATES.md)).
Largest output trees: `outputs_routeB_BEM_v14_stage*` (~12–13 MB each),
`outputs_routeB_BEM_v18_knotplot` (~3 MB).

**Tests:** CLI auditors `test_finite_core_nonspherical_shape_corrections.py`,
`test_pressure_mode_cutoff_delay_stability.py`, `knot-data/knotplot/test_monopole_from_fseries.py`.
No pytest config.

### `SST_horn_bem_research/` (29.6 MB)

| Package | Live? | Entry points |
|---------|-------|--------------|
| `sst_horn_neumann_bem_all_audits/` | **Yes** | `run_horn_bem.py`, `run_horn_sweep.py`, `run_panel_refinement.py`, `run_volume_refinement.py`, `run_offset_probe.py`, `run_all_audits.py` |
| `sst_horn_neumann_bem_package/` | Subset of all_audits | `run_horn_bem.py`, `run_horn_sweep.py` |
| `sst_horn_dirichlet_package/` | Earlier formulation | `run_horn_gates.py` (χ_K + χ_cav → χ_E^hollow) |

Native: `cpp/horn_bem.cpp` / `hornkernels.cpp` via `build_ext_if_needed.py`.
Outputs: `audit_out/`, `audit_out_full/`. No pytest.

### `SST_ssdl_audit_research/` (17.1 MB)

Separatrix Surface-Density Lift (ρ_f^SSDL) Route A BEM DtN + Route B Planck-normal cell count.

| Version | Live |
|---------|------|
| `ssdl_audit/`, **`ssdl_audit_v0_2/`** (0.2.0) | **v0_2** — README, CHANGELOG, `audit_result_v0_2.json` |

Entry: `ssdl_audit_v0_2/run_ssdl_audit.py`. Library: `sst_ssdl_audit/` + `cpp/ssdl_bem.cpp`.

---

## 3. Constants derivation

### `SST_derive_constants_research/` (17.8 MB)

Single unversioned live tree: `code/` (+ manuscripts, `schrodinger_gate/`, audits).
Canonical run order: `README_Derive_Constants.md`. Manifests:
`DERIVED_GATE_EVIDENCE_MANIFEST.json`, `TWO_REMAINING_GATES_MANIFEST.json`.

**Core gate / derivation scripts (`code/`):**

| Script | Computes |
|--------|----------|
| `derive_sector_pressure_volume_factor.py` | Gate 1: 4π/3 per pressure sector |
| `derive_pressure_self_duality_from_laplace_matching.py` | Laplace-matched reciprocal → χ_R=2 |
| `derive_gp_core_profile_second_variation.py` | GP/NLS shell → σ=11/3, c₂=11/48 |
| `derive_relaxed_gp_core_hessian_wperp.py` / `derive_full_gp_field_schur_wperp.py` | w_⊥ gates |
| `solve_one_cell_hodge_phase_hessian.py` | Exterior Hodge → q_φ=1 |
| `derive_phase_pressure_exchange_self_duality.py` | Half-budget → Λ_φ=E_eff/2 |
| `reproduce_alpha_cell_closure.py` | End-to-end α_cell from trefoil coefficients |
| `solve_E0_bem_pressure_cell_nls_batch.py` | Batch BEM+NLS E₀ search |
| `solve_farfield_two_cell_coupling.py` | Two-cell far-field Coulomb certificate |
| `solve_nonlinear_shape_stability.py` (+ scipy117 patch) | N_p shape stability |
| `audit_derived_label_gates.py` | Package-wide claim-status auditor |
| (+ ~15 more `derive_*` / `solve_*` / `audit_*`) | Phase-budget, GP shell deficit, κ asymptotics, ppm closure, … |

**Schrödinger gate:** `schrodinger_gate/sst_schrodinger_gate_constants.py`,
`…_knot_boundary_locking_spectral.py`, `…_r_phase_envelope_symbolic.py`.

**Tests:** `test_finite_core_nonspherical_shape_corrections.py`,
`test_pressure_mode_cutoff_delay_stability.py` (CLI auditors).
**Outputs:** `code/outputs_*` (~17 MB total; largest `outputs_E0_bem_nls_batch_convergence` ~7.8 MB).
Retired solvers under `code/archive/`.

---

## 4. Knot / trefoil / Hopf / catalogue

### `SST_chi_phase_research/` (74.9 MB)

Two parallel lineages:

| Line | Versions | Live |
|------|----------|------|
| Track B GP/NLSE | `sst_chi_phase_package_v10B1` … `v16B0` | **v16B0** — patched Madelung / G5 audit |
| ChiE Biot–Savart / horn-torus | `sstcore_chiE_local0`, `v4`…`v7` | **v7** |

**Track B entry (newest):** `sst_chi_phase_package_v16B0/simulate_chi_phase_v16B0.py`
(+ pure-Python `sst_chi_phase_v16B0_py.py`). Each prior `v*B0` has matching `simulate_chi_phase_v*.py`.

**ChiE v7 entry points:**

| Script | Computes |
|--------|----------|
| `simulate_trefoil_biot_closure.py` | Ideal-trefoil Biot–Savart self-energy / closure |
| `simulate_horn_torus_chiE.py` | Horn-torus χ_K, χ_cav, χ_E |
| `simulate_epsilon_sweep.py` | Softening ε sweep |
| `simulate_mass_mode_comparison.py` | Kinetic / cavity / vacuum-subtracted modes |
| `simulate_trefoil_thickness_audit.py` | Thickness / ropelength vs ideal |
| `simulate_solid_core_constant_density.py` | Rankine-core toroidal tube χ_E |
| `run_chiE_bulk_matrix.py` | Option matrix over λ, ε, quadrature, kernel, mass mode |

**Tests:** `test_horn_torus_chiE.py`, `test_solid_core_constant_density.py` (run as scripts).
**Outputs:** per-package `exports/` (v7 ~5.7 MB). Nested `legacy_v10B1_reference` /
`legacy_v11B0_reference` are exact `.py` copies of prior versions.

### `SST_Trefoil_Closure/` (182.7 MB)

Merged trefoil / robustness / early chi-phase (v1–v6, **different lineage** from
`SST_chi_phase_research` v10B1–v16B0).

| Area | Live |
|------|------|
| Knot robustness | `sst_knot_candidate_robustness_sweep_v10_3_master_sweep.py` |
| Chi-phase (this tree) | `sst_chi_phase_package_v6/` (superseded globally by chi_phase_research v16B0) |
| Multisector / GUI | root GUIs + `_dashboard_conflict/` staging (Aug 2026) |

**Other root runners:** `sst_ideal_trefoil.py`, `main.py` (C++ `sst_closure_lab`),
`trefoil_multisector_fitter.py` / `v2`, `simulate_macro_wake.py`, `simulate_lorentz.py`,
`SST_ATOM_MASS_INVARIANT_SEMF_patched.py`, taxonomy builders under `sst_taxonomy_starter_v*`.
**Outputs:** `exports/` ~38 MB. **Archive:** 30 retired scripts under `archive/`. No pytest.

### `SST_ideal_trefoil_biot_research/` (2.7 MB)

| Package | Entry | Note |
|---------|-------|------|
| `sst_ideal_trefoil_biot_package_v2/` | `simulate_trefoil_biot_closure.py` | Byte-identical to chiE v7 copy |
| `sst_trefoil_bs/` | `trefoil_energy.py` | Full ideal.txt → BS → Compton pipeline |
| `sst_3d_collider_robust/` | `embed_ideal_favorites.py` | Browser collider (JS), not batch calc |

### `SST21D_knot_order_pipeline/` (19.9 MB)

| Versions | Live |
|----------|------|
| `v0.1.0`, **`v0.2.0`** | **v0.2.0** — Fresnel `.fseries`/`.short` + Gilbert |

Primary CLI: `py -3 -m sst21d` (`list`, `static`, `fresnel-scan`, `fresnel-static`,
`fresnel-convergence`, `fresnel-export`, `dynamic`, `analyze-xyz`, `make-rr-bridge`,
`build-native`). Wrappers: `scripts/run_static_favorites.py`, `generate_demo_trajectory.py`.

**Tests:** `tests/test_fresnel.py`, `test_gilbert.py`, `test_geometry.py`, `test_order.py`
with `[tool.pytest.ini_options]` in `pyproject.toml`.
**Outputs:** `outputs/` ~4.7 MB; `exports/fresnel_ridgerunner/` ~8 MB.

### `SST_Hopf_Benchmark/` (0.2 MB)

Packet `SST_Hopf_Benchmark_Packet_v0.1/` — eight numbered H-gate scripts
(`01_definieer_sst_orderparameter.py` … `08_trefoil_integratie.py`) + `sst_hopf_common.py`.
Smoke: `tests/run_smoke.py`. No pytest.ini.

---

## 5. Falsifiers / predictions / routes

### `SST_dimensionless_dynamic_predictions/` (279.4 MB)

| Versions | Live |
|----------|------|
| v0.1.0, v0.2.0 infinite-background, v0.3.0 axial-bundle, **v0.4.0 iso-Γ/A clock** | **v0.4.0** |

| Module / tool | Computes |
|---------------|----------|
| `src/sst_dimensionless_ratios.py` (`sst-ratios`) | Biot–Savart evolution, relative-equilibrium residuals, recurrence |
| `src/sst_axial_vortex_bundle.py` (`sst-axial-bundle`) | Trefoil in axial vortex-tube bundle |
| `src/sst_iso_gamma_area_clock.py` (`sst-iso-gamma-area`) | C9 iso-Γ/A dynamic-clock falsifier |
| `tools/analyze_iso_gamma_area.py` | Post-process C9 campaigns / Q_Γ=1 gates |
| `tools/analyze_bundle_modes.py` | Physical-tube vs discretization campaigns |
| `tools/analyze_background_invariance.py` | Zero vs solid-body background pairs |

**Tests:** `tests/test_*.py` (18 claimed in RELEASE_NOTES); no pytest.ini — run via `batch/*_selftest.bat`.
**Outputs:** v0.4 `outputs/` ~3 MB; v0.3 `outputs/` ~45 MB (largest campaign tree).

### `SST_contact_billiard_hydrodynamic_falsifier/` (365.9 MB)

| Versions | Live |
|----------|------|
| v0.1.0, **v0.2.0** | **v0.2.0** — full research matrix, bundled Gilbert DB |

| Entry | Computes |
|-------|----------|
| `sstcbhf/cli.py` (`sst-cbhf`) | `analyze`, `demo`, convergence, H0–H8 gate ledger |
| `scripts/run_all_research.py` | Resumable research matrix (`quick`/`full`/`max`/`extreme`) |
| Package modules | `billiard.py`, `contact.py`, `hydrodynamics.py`, `force_balance.py`, `gates.py` |

**Tests:** `tests/test_*.py` with `[tool.pytest.ini_options]` in `pyproject.toml`.
**Outputs:** `outputs/` ~65 MB; `validation_outputs/` ~12 MB. Nested `.venv/` ~280 MB.

### `SST_minimal_falsification_harness/` (1.3 MB)

| Versions | Live |
|----------|------|
| v0.1.0, v0.2.0_Gilbert (nested folder), **v0.3.0** | **v0.3.0** |

Entry: `sst_minimal_falsification.py` (`demo`, `audit`, `template`, `features`,
`gilbert-batch`, `batch-predict`); `upgrade_calibration_json.py`.
No pytest — BAT self-tests only.

### `SST_Sutcliffe_HSS_feasibility_gate/` (0.1 MB)

Only `Sutcliffe_HSS_feasibility_gate_v0.1.0/`. Entry: `run_all.py` →
`src/nonlocal_circle.py`, `identifiability.py`, `sector_seeds.py`.
Zip sits **inside** the extracted folder. Outputs: `outputs/` (~0.06 MB).

### `SST_dark_knot_rayleigh_research/` (1.0 MB)

Single harness: `SST_dark_knot_rayleigh_harness/`.
`run_example.py`, `run_sweep.py`, `run_all_checks.py`, `ideal_favorites_to_csv.py`,
`make_response_pair_proxy.py`. Library: `sst_dark_knot_harness/`. Outputs: `audit_out/`.

### `SST_Route_I_relative_entropy_PoC/` (6.9 MB)

**Only `v0.0.4` is extracted.** Nine archives exist; newest `v0.1.0` was never unpacked.
Scripts that live only inside those zips are listed in
[INVENTORY_ARCHIVES.md](INVENTORY_ARCHIVES.md).

| On disk | Computes |
|---------|----------|
| `…_v0.0.4/sst_relative_entropy_route1_poc_v0.0.4.py` | Boundary microstates, η_A^SST, Gaussian KL → S_rel, no-go for r_c piercings |
| `…_v0.0.4/sst_relative_entropy_route1_poc_v0.0.3.py` | Base module (torsion / Rindler / KMS) |
| `routeI_heat_guard_patch_bundle_v0_8_19/apply_routeI_impedance_patch_v0_8_19.py` | Canon heat-guard patch applicator |
| *(zip-only)* `sst_route1_resolved_knot_action_v0.1.0.py` | Resolved-knot action I_K, Ω_K, β_Q ladder |

### `SST_v0_8_19_routes_research/` (7.7 MB)

| Pack | Role |
|------|------|
| **`SST_v0_8_19_Planck_Routes_v3_preregistered_all_inclusive_pack/`** | Live — supersedes earlier A–D packs |
| `…_A_to_D_equivalence_corrected_pack/` | Superseded v2 corrected |
| `…_RouteA_parallel_derivation_falsification_pack/` | Three preregistered σ_pierce × Λ_L families |
| `sst_nonfit_prediction_harness_v0_8_19/` | Four closure gates reporter |
| `sst_torsion_impedance_pybind11_v0.8.19_autobuild/` | Torsion impedance audit (native or NumPy) |

Live scripts: `scripts/route_ABCD_equivalence_scan_audit_v3.py`,
`routeA_preregistered/routeA_vacuum_tangle_preregistered_target.py`,
`nonfit_harness.py`, `audit_impedance.py`.
Tests: `test_nonfit_harness.py`, `test_impedance.py`. Archive trees under
`v3…/archive/legacy_*` (extracted v2 duplicate + zips).

---

## 6. Coil / hardware

### `SST_Coil_DigitalTwin_research/` (27.3 MB)

Versions: `v1`, `v4`, `v5`, `v7`, `v8_exact_rodin`, `v9_complete`, **`v10_complete_restored`**
(no v2/v3/v6). Live: **v10**.

Orchestrator: `SST_Coil_90_RunAll.py` → geometry → PWM → Biot–Savart → observables →
radius scaling → compare. Modules `SST_Coil_10_*` … `SST_Coil_80_*`, `SST_Coil_99_validate.py`.
`legacy_all_versions_from_user_zip/` holds 38 archived scripts (duplicates of older versions).
Outputs: `exports/SST-Coil/run_YYYYMMDD_HHMMSS/`.

### `SST_CoilLab_research/` (9.8 MB)

| Versions | Live |
|----------|------|
| `SST_CoilLab_v1`, **`SST_CoilLab_v2_work`** | **v2_work** — adds mutual inductance |

`run_all.py`, `validate.py`; packages `geometry/`, `physics/`, `experiments/`, `visualization/`.
v2-only: `physics/mutual_inductance.py`, `current_mutual.py`, `experiments/mutual_current_sweep.py`.

### `GUI/coils/` (18 scripts)

Iterative Rodin / SawShape / Starship Tk GUIs. Live end of line:
`rodin_GUI3_v15_sst_gravity_proxy.py` (v11–v15 branch). Also `GUI-SawBowl.py`,
`rodin_GUI.py` / `GUI2`, Halbach / starshaped helpers.

### `3D/Python/`

Standalone STL / Blender generators. Live lines:

- Grooved torus: `blender_grooved_torus_6lanes_full_v5_fix_cyclic_majoroffset_singleboolean.py`
- Clamshell mold: `blender_rodin_winding_core_multisize_clamshell_v7.py`
- Reference geometry: `rodin_6lane_channel_guide_knot512.py` (copied into Coil `original_sources/`)

Many near-duplicates (`pythonai.py`, `Rodin_Coil_6_phases.py`, `…(1).py`).

---

## 7. Audits / bridges

### `SST_fs_attachment_audit_research/` (114.2 MB)

Primary: `fs_core/fs_unified_attachment_audit.py` (+ `_v4`, `_MAXHR`, `_v0` variants).
Twist / holonomy: `fs_core_twist_audit_v2.py` → `fs_core_holonomy_audit_v2_canon_core_cycle.py`.
Also attachment lemma / compensated / swirl-clock / gear-locked audits; Hopfion
`fs_relax2.py`, `fs_relax_xpu.py`, production-run variants; `hopfion/hopfion_tools.py`;
Blender `geometry/trefoil_core_helix_blender_script.py`.
Outputs: scattered CSV/MD + `fs_core/exports/` (~0.5 MB); bulk of 114 MB is audit results.

### `SST_contra_swirl_bridge_research/` (2.6 MB)

Progressive standalone falsifiers (no v0_5 folder):

| Version | Script | Adds |
|---------|--------|------|
| v0 | `sst_contra_swirl_bridge_test.py` | Circulation neutrality, helicity proxy |
| v0_2 | `…_v0_2.py` | Decoherence / chirality / distance scans |
| v0_3 | `…_v0_3.py` | Experimental CSV fit to R_χ(t,L,T) |
| v0_4 | `…_v0_4_spectral_epr.py` | Eckvahl EPR field-sweep chirality |
| **v0_6** | `…_v0_6_timefield_supplement_audit.py` | Spectral + PDF timefield → writes `SST_timefield_spectral_v06_research/` |

### `SST_timefield_spectral_v06_research/` (26.9 MB)

**No Python** — output archive from contra-swirl v0_6
(`timefield_long_v06.csv` ~17.9 MB, spectral CSVs, audit JSON, PNGs).

---

## 8. Pipelines / legacy / dashboard / datasets / scripts

### `KnotPlot/ridgerunner/` (25 Python files)

KnotPlot relaxation → seed selection → VECT → ridgerunner tightening → catalogue status.

| Script | Role |
|--------|------|
| `run_build_batch.py` | Batch KnotPlot builds |
| `select_knotplot_seed.py` | Pick best trial for RR |
| `run_knotplot_txt.py` | RR on KnotPlot XYZ `.txt` |
| `run_catalog_knot.py` / `run_catalog_batch.py` | Three-stage + N-ladder from fseries |
| `run_ideal_knot.py` | Gilbert AB → RR at multiple N |
| `fseries_to_xyz.py` / `gilbert_ab_to_xyz.py` | Samplers |
| `effort_presets.py`, `_ladder_plan.py`, `_recover_ladder_coarse.py`, `count_rr_la_failures.py` | Effort / LA-failure recovery |
| `classify_catalog_status.py`, `parse_knotplot_log.py` | Status / log sidecars |

**Tests:** 11 `test_*.py` under `ridgerunner/` (unittest-style).
Root helpers: `knotplot_txt_to_vect.py`, `resample_closed_knot_txt.py`,
`gilbert_reader.py`, `ideal_resolver.py`, `build_knotplot_knots_data.py`,
`make_ideal_3_1_from_knotplot_radius.py`.

### `KnotPlot/knots/` (11 Python files)

`knot_batch_v2/v3/v4.py`, `raw_2_fseries.py`, `fseries_compat.py`, `sst_exports.py`,
`sst_helicity_balance_scan.py`, `oriented_link_scores.py` / `v2`,
`rank_monopole_candidates_v2.py`, `test_monopole_from_fseries.py`.

### `proof-scripts/`

| Tree | Role |
|------|------|
| `sstcore/examples/` | SSTcore demos: helicity, braids, ab-initio mass, hydrogen spectrum, Taichi, SnapPy |
| `swirl/SST_Mathematical_Proof_Python/` | GR/VAM benchmarks, fseries computations, Streamlit coil app, Biot–Savart GUIs |
| `swirl/VAM_Python_Benchmarks/` | Near-duplicate of `Python_Benchmarks/` (19/20 byte-identical) |
| `swirl/VAM_PYTHON_SIMULATOINS/` | Typo name; **distinct** content — QC/CHSH, VAM-lab, inference, knot workbench |

Key files: `SSTcore_full_probe.py`; `Python_Benchmarks/VAM_Benchmark.py`, `GR_VS_VAM.py`;
`Python_Computations/VAM_Fseries/fseries.py`; `StreamLitApp_Coil_builder/app.py`;
`VAM_PYTHON_SIMULATOINS/vam_knot_workbench.py`, `canonical_vam_chsh*.py`,
`VAM-lab/vam_lab_gui.py` / `VAM-lab2/…`.

### `SST-dashboard/`

Entry: `sst_dashboard_app.py` (PyQt5). Tabs under `gui_tabs/`:
`tab_knot_fseries_master.py`, `tab_knot_robustness_v10_3.py`, `tab_fseries_tools.py`,
`tab_ab_initio.py`, `tab_mass_sweep.py`, `tab_hydrogen.py`, `tab_theory.py`, …
Plus `sst_ffs_research_package/scripts/`.

### `datasets/*.py`

Gravity / swirl visualizers (`grav.py`…`grav3.py`, `gravity_hierarchy.py`,
`SwirlVSGauge.py`, …), particle classification, SPARC inverse reconstruction
(`SPARC/sst_sparc_inverse_reconstruction_v2.py`).

### `scripts/` (repo maintenance)

`reorg_to_be_processed.py`, `reorg_derive_constants.py`, `merge_sst_dashboard.py`,
`merge_trefoil_closure.py`, `merge_closure_sstcore_swirl.py` + matching `test_*.py`
(pytest, 15 tests).

### Root

| File | Role |
|------|------|
| `sst_gilbert_usability.py` | Gilbert ideal usability gate via contact score C_cont |
| `test_sst_gilbert_usability.py` | unittest (4 tests) |

### `verification-suites/`

Only `embedded-knots/test_embedded_knots.py` (pytest; skips if SSTcore C++ missing).

### `templates/SST_cpp_pybind_audit_template/`

`run_example.py`, `run_sweep.py`, `run_all_checks.py` + `native_ext/build_ext_if_needed.py`.

---

## Testing reality (Workbench-wide)

| Pattern | Where |
|---------|-------|
| Real `[tool.pytest.ini_options]` | `SST21D_knot_order_pipeline` v0.2.0, `SST_contact_billiard_hydrodynamic_falsifier` v0.1/v0.2 |
| Standalone `test_*.py` / `run_all_checks.py` audit batteries | Fermat, dark-knot, horn, Hopf, Coil validate, most research packs |
| Repo-root unittest | `test_sst_gilbert_usability.py` |
| Repo-root pytest (reorg helpers) | `scripts/test_*.py` |
| **No** root `pytest.ini` / `pyproject.toml` / `conftest.py` | — |

Most “tests” in research packs are **CLI falsification runners**, not automated CI suites.
