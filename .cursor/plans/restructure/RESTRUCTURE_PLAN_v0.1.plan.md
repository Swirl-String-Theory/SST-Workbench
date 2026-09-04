# RESTRUCTURE PLAN v0.1 — all 73 roots to exact destinations

Status: `PLANNED` · Baseline: 2026-09-03

The one-time mapping. Every current top-level directory appears exactly once. When the migration
finishes, this document is history; [CATALOG_v0.1.md](CATALOG_v0.1.md) is what remains.

This is the human-readable source for `10_docs/migration/path_map.csv`, generated in SP00. Where
the two disagree, the CSV wins — it is the machine-checked artifact.

## Path abbreviations used in the tables

| Short | Full |
|-------|------|
| `R/A` | `01_research/A_falsifiers/` |
| `R/B` | `01_research/B_closures/` |
| `R/C` | `01_research/C_dynamics/` |
| `R/D` | `01_research/D_benchmarks/` |
| `R/E` | `01_research/E_pipelines/` |
| `R/F` | `01_research/F_exploratory/` |
| `L/A` `L/B` `L/C` `L/D` | `02_libraries/{A_knot_geometry,B_knot_data,C_finite_core,D_numerics}/` |
| `D/A` `D/B` `D/C` `D/D` | `03_data/{A_knots,B_external,C_reference,D_generated}/` |
| `T/A` `T/B` `T/C` `T/D` | `04_tools/{A_geometry,B_crawlers,C_fabrication,D_proof}/` |
| `APP` | `05_apps/` |

Version directories keep their current long names throughout stage 1. SP09 renames them to
`<ID>-vX.Y.Z`.

---

## 1. Simple moves — one root, one destination

These need no semantic decision. Move the whole tree, leave a junction.

| # | Current root | Destination | Kind | Phase |
|---|--------------|-------------|------|-------|
| 1 | `Fremlin_FourierSeries/` | `D/A/A006_fremlin_fourier_series/` | data | SP04 |
| 2 | `generated-figures/` | `D/D/D002_figures/` | output | SP04 |
| 3 | `Ideal_Sources/` | `D/A/A004_ideal_gilbert/` | data | SP04 |
| 4 | `Independent_FiniteCore_SpectralSelector/` | `L/C/C001_finite_core_spectral_selector/` | code | SP05 |
| 5 | `Katlas_Source_Crawler_v0.2.2/` | `T/B/B001_katlas_source_crawler/v0.2.2/` | tooling | SP04 |
| 6 | `Katlas_Sources_v0.2.2_Outputs/` | `D/A/A005_katlas_sources/v0.2.2/` | data | SP04 |
| 7 | `Knot_Geometry_Library/` | `L/A/A001_knot_geometry_library/` | code | SP05 |
| 8 | `KnotTheory/` | `08_third_party/knot_theory/` | vendored | SP04 |
| 9 | `media/` | `D/C/C001_media/` | data | SP04 |
| 10 | `proof-scripts/` | `T/D/D001_proof_scripts/` | tooling | SP04 |
| 11 | `PTSA_Parametric_Trefoil_Seed_Atlas_v1.0.0/` | `D/A/A008_parametric_trefoil_seed_atlas/v1.0.0/` | data | SP04 |
| 12 | `Restore_Archives/` | `09_archive/restore/` | archive | SP04 |
| 13 | `scripts/` | `07_scripts/` | tooling | SP04 |
| 14 | `SST-dashboard/` | `APP/A001_dashboard/` | app | SP04 |
| 15 | `templates/` | `06_templates/` | tooling | SP04 |
| 16 | `datasets/` | `D/B/B001_sparc_and_papers/` | data | SP04 |
| 17 | `bundles/` | `09_archive/bundles/` | archive | SP04 |
| 18 | `verification-suites/` | `R/D/D001_embedded_knots_verification/` | code | SP05 |

`scripts/` becoming `07_scripts/` changes the documented test command from `python -m pytest scripts/`
to `python -m pytest 07_scripts/`. `07_scripts` is not importable as a Python package; SP03 verifies
nothing relies on that.

---

## 2. Clean family moves — root already equals one family

Version directories inside are already a coherent series. Move the root, rename it to its catalog
family directory, leave a junction.

| # | Current root | Destination | Versions | Phase |
|---|--------------|-------------|---------:|-------|
| 19 | `SST_6Source_Blind_Falsifier_v0.1.0/` | `R/A/A018_six_source_blind/` | 1 | SP05 |
| 20 | `SST_7Article_Closure_Holonomy/` | `R/A/A024_seven_article_closure_holonomy/` | 3 | SP05 |
| 21 | `SST_Breathing_Stretching_Return_Phase_Causality/` | `R/A/A031_breathing_stretching_return_phase_causality/` | 1 | SP05 |
| 22 | `SST_Chiral-Kelvin-Mode/` | `R/A/A005_chiral_kelvin_mode/` | 5 | SP05 |
| 23 | `SST_Chirality_Helicity_Transport_Polarity/` | `R/A/A036_chirality_helicity_transport_polarity/` | 2 | SP05 |
| 24 | `SST_Coil_DigitalTwin_research/` | `R/F/F003_coil_digital_twin/` | 7 | SP05 |
| 25 | `SST_CoilLab_research/` | `R/F/F002_coil_lab/` | 2 | SP05 |
| 26 | `SST_contact_billiard_hydrodynamic_falsifier/` | `R/A/A001_contact_billiard_hydrodynamic/` | 2 | SP05 |
| 27 | `SST_contra_swirl_bridge_research/` | `R/F/F008_contra_swirl_bridge/` | 5 | SP05 |
| 28 | `SST_counterpulley_alpha_falsifier/` | `R/A/A007_counterpulley_alpha/` | 2 | SP05 |
| 29 | `SST_dark_knot_rayleigh_research/` | `R/F/F006_dark_knot_rayleigh/` | 1 | SP05 |
| 30 | `SST_derive_constants_research/` | `R/B/B001_derive_constants/` | unversioned | SP05 |
| 31 | `SST_dimensionless_dynamic_predictions/` | `R/A/A002_dimensionless_dynamic_predictions/` | 4 | SP05 |
| 32 | `SST_fermat_pybind_research/` | `R/C/C007_fermat_biot_savart/` | 12 | SP05 |
| 33 | `SST_Finite_Core_Axial_Toroidal_Phase_Delay/` | `R/A/A025_finite_core_axial_toroidal_phase_delay/` | 3 | SP05 |
| 34 | `SST_Fourier_vs_Ideal_Blind_Falsifier/` | `R/A/A019_fourier_vs_ideal/` | 2 | SP05 |
| 35 | `SST_fs_attachment_audit_research/` | `R/F/F001_fs_attachment_audit/` | unversioned | SP05 |
| 36 | `SST_Helmholtz/` | `R/A/A010_helmholtz_vortex_gates/` | 2 | SP05 |
| 37 | `SST_ideal_links/` | `R/D/D003_ideal_links_test_suite/` | 14 | SP05 |
| 38 | `SST_Katlas_Link_Geometry_Conditioning_v2.0.0/` | `R/E/E003_katlas_link_geometry_conditioning/v2.0.0/` | 1 | SP05 |
| 39 | `SST_Material_Phase_EFT/` | `R/A/A029_material_phase_eft/` | 2 | SP05 |
| 40 | `SST_minimal_falsification_harness/` | `R/A/A003_minimal_falsification_harness/` | 3 | SP05 |
| 41 | `SST_Phase_Feedback_Delay_Knot_Stability/` | `R/A/A026_phase_feedback_delay_knot_stability/` | 4 | SP05 |
| 42 | `SST_preferred_frame_binary_falsifier/` | `R/A/A006_preferred_frame_binary/` | 2 | SP05 |
| 43 | `SST_Quantum_Galileo_Action_Gauge_Closure/` | `R/A/A039_quantum_galileo_action_gauge_closure/` | 2 + key | SP05 |
| 44 | `SST_ssdl_audit_research/` | `R/B/B008_ssdl_audit/` | 2 | SP05 |
| 45 | `SST_Sutcliffe_HSS_feasibility_gate/` | `R/A/A004_sutcliffe_hss_feasibility_gate/` | 1 | SP05 |
| 46 | `SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier/` | `R/A/A037_trefoil_dynamic_seed_qualification/` | 7 + 1 odd | SP05 |
| 47 | `SST_vArrow_Spectral_Blind_Falsifier/` | `R/A/A027_varrow_spectral/` | 3 | SP05 |
| 48 | `SST21D_knot_order_pipeline/` | `R/E/E001_sst21d_knot_order/` | 2 | SP05 |
| 49 | `Trefoil_Balance_to_TBK_RPO_Handoff_v0.1.0/` | `R/E/E002_trefoil_balance_tbk_rpo_handoff/v0.1.0/` | 1 | SP05 |
| 50 | `Wien_Planck_SST_Field_Matter_Closure/` | `R/A/A040_wien_planck_field_matter_closure/` | 6 | SP05 |
| 51 | `SST_routeB_RT_bem_research/` | `R/B/B002_route_b_rt_bem/` | 22 + shared | SP05 |

**Pilot.** #46, `SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier`, is the first family moved.
It has a clean `v0.1.0 … v0.3.1` series, 401 tracked files, and only 34 files in the break-set. Its
one anomaly, `SST_Trefoil_v0.3.0_with_Knot_Library_v0.2.5`, is a *variant* of v0.3.0 and becomes
`v0.3.0+knotlib0.2.5` recorded in `FAMILY.yaml`, not a version of its own.

**#43** carries `_BLIND_SOURCE` and `_REVEAL_KEY` siblings of v0.1.1. These are variants, not
versions: see §5.

**#51** mixes 22 versions with shared `demos/`, `knot-data/`, `outputs/` and `shared/`. The
versions move to the family; `outputs/` and `shared/` go to `D/D/D004_routeb_shared_outputs/`;
`knot-data/` goes to `D/A/`. Confirm before moving.

---

## 3. Container splits — one root, several families

These need semantic classification, not a blind `git mv`. Full per-container detail in
[SP06](SP06_container_splits.plan.md).

| # | Current root | Splits into | Count | Phase |
|---|--------------|-------------|------:|-------|
| 52 | `SST_Maxwell/` | `R/A/{A011,A012,A013,A014,A015,A016}` | 6 | SP06 |
| 53 | `SST_Intrinsic_Modal_Swirl_Clock/` | `R/A/{A032,A034,A035,A038}` | 4 | SP06 |
| 54 | `SST_Threaded_Hole_Substrate_Blind_Falsifier_v0.1.0/` | `R/A/{A022,A023}` | 2 | SP06 |
| 55 | `SST_Trefoil_Lobe_Orientation_Blind_Falsifier/` | `R/A/{A020,A021,A030}` | 3 | SP06 |
| 56 | `SST_Einstein/` | `R/A/{A008,A009}` | 2 | SP06 |
| 57 | `SST_Kelvin_Floquet/` | `R/A/{A017,A028}`, `R/C/C008` | 3 | SP06 |
| 58 | `SST_Hopf_Benchmark/` | `R/D/{D002,D004}` | 2 | SP06 |
| 59 | `SST_chi_phase_research/` | `R/C/{C001,C002}` | 2 | SP06 |
| 60 | `SST_v0_8_19_routes_research/` | `R/B/{B003,B004,B005}`, `R/C/C004`, `R/F/F005` | 5 | SP06 |
| 61 | `SST_horn_bem_research/` | `R/B/{B006,B007}` | 2 | SP06 |
| 62 | `SST_ideal_trefoil_biot_research/` | `R/C/{C003,C005}`, `L/D/D001` | 3 | SP06 |
| 63 | `SST_Route_I_relative_entropy_PoC/` | `R/F/{F004,F007}` | 2 | SP06 |
| 64 | `SST_QHP_Stability_Landscape/` | `R/A/A033`, `T/A/A003` | 2 | SP06 |
| 65 | `SST_Trefoil_Closure/` | `R/C/C001`, `R/F/F009`, `D/D/` | 2 + outputs | SP06 |
| 66 | `GUI/` | `APP/{A002,A003,A004}`, `R/C/C006`, `D/C/C002` | 4 + assets | SP06 |
| 67 | `Knot_Library/` | `L/B/B001`, `D/A/A007` | 2 | SP06 |
| 68 | `3D/` | `T/C/C001` (source), `D/D/D001` (STL, G-code) | 2 | SP06 |

`SST_QHP_Stability_Landscape/` is the clearest example of why this phase cannot be automated: it
contains `SST_KnotPlot_QHP_Sweep_Generator_v0.1.0`, which *produces* the data the falsifier
consumes. A generator and its consumer are not versions of each other.

---

## 4. KnotPlot — its own refactor

`KnotPlot/` is ~12.4 GB and currently holds four different kinds of thing. Full detail in
[SP07](SP07_knotplot_refactor.plan.md).

| # | Current sub-path | Destination | Kind | Approx. size |
|---|------------------|-------------|------|-------------:|
| 69a | `KnotPlot/*.py`, `*.kps`, `*.lnk`, `run_build*.cmd` | `T/A/A001_knotplot/` | tool | small |
| 69b | `KnotPlot/ridgerunner/` excl. `out/` | `T/A/A002_ridgerunner/` | tool | ~50 MB |
| 69c | `KnotPlot/knots/` | `D/A/A001_knotplot_relaxed/` | data | ~7.8 GB |
| 69d | `KnotPlot/Knots_FourierSeries/` | `D/A/A002_knotplot_fourier_series/` | data | ~0.7 MB |
| 69e | `KnotPlot/qhp*/` | `D/A/A003_knotplot_qhp/` | data | ~29 MB |
| 69f | `KnotPlot/ridgerunner/out/` | `D/D/D005_knotplot_campaign_outputs/` | output | ~3.9 GB |
| 69g | `KnotPlot/Trefoil_Balance_Point_Campaign_v*` | `R/E/E004_knotplot_trefoil_balance_point/` | campaign | ~413 MB |
| 69h | `KnotPlot/KnotPlot_3p1_Trefoil_Seed_Campaign_v*` | `R/E/E005_knotplot_trefoil_seed/` | campaign | ~133 MB |
| 69i | `KnotPlot/KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v*` | `R/E/E006_knotplot_multidynamics_relaxation_matrix/` | campaign | ~85 MB |
| 69j | `KnotPlot/KnotPlot_3p1_Comprehensive_Dynamics_Parameter_Atlas_v*` | `R/E/E007_knotplot_dynamics_parameter_atlas/` | campaign | ~188 MB |
| 69k | `KnotPlot/KnotPlot_3p1_MissingParameter_Command_Certification_v*` | `R/E/E008_knotplot_command_certification/` | campaign | ~2 MB |
| 69l | `KnotPlot/KnotPlot_MultiTopology_QHP_Sweep_v*` | `R/E/E009_knotplot_multitopology_qhp_sweep/` | campaign | ~99 MB |
| 69m | `KnotPlot/*_outputs.zip` (17 files) | `09_archive/restore/KnotPlot/` | archive | — |

The conceptual point this refactor buys:

```text
generator/tool  !=  input geometry  !=  campaign  !=  campaign result
```

All four currently live under `KnotPlot/`.

---

## 5. Variants that are not families and not versions

These stay inside their family, next to the version they belong to. They never get a catalog ID and
never become a version directory.

| Current | Belongs to | Placement |
|---------|------------|-----------|
| `SST_Quantum_Galileo_..._v0.1.1_BLIND_SOURCE/` | A039 v0.1.1 | `A039_.../v0.1.1/` (the version itself) |
| `SST_Quantum_Galileo_..._v0.1.1_REVEAL_KEY/` | A039 v0.1.1 | `A039_.../keys/v0.1.1_REVEAL_KEY/` |
| `SST_Maxwell/3_Maxwell_SST_Physical_Lines_Unblind_Key_v0.2.0/` | A013 v0.2.0 | `A013_.../keys/v0.2.0_UNBLIND_KEY/` |
| `SST_Maxwell/3_SST_Maxwell_Blind_Unblind_Key_v0.1.0/` | A014 v0.1.0 | `A014_.../keys/v0.1.0_UNBLIND_KEY/` |
| `SST_Trefoil_..._Mega_Falsifier/SST_Trefoil_v0.3.0_with_Knot_Library_v0.2.5/` | A037 v0.3.0 | `A037_.../variants/v0.3.0+knotlib0.2.5/` |

Blind and revealed artifacts are never merged. `keys/` is gitignored by default and its contents
are registered in `FAMILY.yaml`, not committed, unless the family is explicitly unblinded.

---

## 6. Stubs and deletions

Nothing here is deleted before SP11, and SP11 only runs after SP10 passes.

| # | Current root | Disposition | Phase |
|---|--------------|-------------|-------|
| 70 | `to_be_processed/` | delete — one relocation `README.md`, content moved long ago | SP11 |
| 71 | `experiments/` | `experiments/sycl/` to `R/F/F010_sycl_probes/`; `derive_constants/` and `trefoil/` are stubs, delete | SP06 / SP11 |
| 72 | `falsifier_registry/` | `README.md` to `10_docs/registry/`; directory deleted. `falsifier_registry.yaml` stays at repo root | SP04 / SP11 |
| 73 | `SST_timefield_spectral_v06_research/` | output-only, to `D/D/D003_timefield_spectral/` | SP05 |

## Non-root items also handled

| Item | Disposition | Phase |
|------|-------------|-------|
| `.tmp.driveupload/` (~5.65 GB, 11 files) | Google Drive staging, not research content. Excluded from the migration; disposition decided separately | SP11 |
| Root `*.zip` (Katlas 24 MB, routeB 29 MB, PTSA 0.8 MB) | `09_archive/restore/` under the existing theme rules | SP04 |
| Root `INVENTORY*.md`, `MIGRATION_MANIFEST.md`, `MOVE_*.md`, `WORKBENCH_LAYOUT.md`, `CONFLICT_RESOLUTION.md` | `10_docs/inventory/` and `10_docs/migration/` | SP04 |
| Root `sst_gilbert_usability.py` + its test, `rhof_eligibility_scan.py` | `07_scripts/` | SP04 |
| Root `knots_ideal_favorites.txt`, `rhof_triage.csv` | `D/A/A004_ideal_gilbert/` | SP04 |
| `README.md`, `.gitignore`, `.gitattributes`, `falsifier_registry.yaml`, `requirements-workbench.txt` | stay at repo root | — |

---

## Summary

| Category | Roots | Sub-plan |
|----------|------:|----------|
| Simple moves | 18 | SP04 |
| Clean family moves | 33 | SP05 |
| Container splits | 17 | SP06 |
| KnotPlot refactor | 1 | SP07 |
| Stubs and deletions | 4 | SP06 / SP11 |
| **Total** | **73** | |

73 roots become 109 catalog identities in 10 domains. The 36 net new identities are families that
already existed scientifically but had no independent existence in the filesystem.
