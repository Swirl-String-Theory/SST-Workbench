---
name: SST Workbench inventory
overview: "Write four inventory documents in the SST-Workbench root: a project overview, a catalog of the research Python calculation scripts, a full archive (zip) overview, and a report of the nested/duplicated working directories found across all 4160 directories."
todos:
  - id: overview
    content: "Write INVENTORY.md: repo purpose, per-top-level-directory size/file-count/role table, classification of the ~30 root folders into research packs / data / tooling / vendored / stubs, flag .tmp.driveupload and the nested .venv, note where README.md and WORKBENCH_LAYOUT.md are stale, cross-link the other docs"
    status: completed
  - id: python
    content: "Write INVENTORY_PYTHON.md: per research pack, grouped by theme (Fermat, BEM, constants, knot/trefoil, falsifiers, coil, audits, pipelines) - purpose, version folders, live version + evidence, entry-point scripts with one-line descriptions, tests, output locations; close with a section on the actual state of testing"
    status: completed
  - id: archives
    content: "Write INVENTORY_ARCHIVES.md as bundles (zip + same-named version folder = one unit): 87 paired, 51 zip-only never unpacked here, plus folder-only cases; lead with the 13 Python scripts that exist only inside archives (8 of them the unextracted SST_Route_I lineage incl. the newest v0.1.0); then largest archives, data-only orphans, repeated identical archives, and the .gitignore exclusion"
    status: completed
  - id: duplicates
    content: "Write INVENTORY_DUPLICATES.md: nesting and duplication findings grouped by kind (dir-in-dir, stale output in newer version, embedded legacy copies, whole-tree duplication, near-identical version pairs, cross-pack file copies, duplicate downloads, merge leftovers, non-source bulk) with paths and evidence, no recommendations"
    status: completed
  - id: verify
    content: Run the two root test suites (unittest test_sst_gilbert_usability, pytest scripts/) to confirm nothing was disturbed, and re-read the four new docs for internal consistency of the numbers
    status: completed
isProject: false
---

# SST-Workbench inventory

Documentation-only change. Four new markdown files in `c:\workspace\projects\SST-Workbench\`, no code touched.

## Measured baseline (already gathered)

- 4160 directories, ~11.9 GB tracked content, plus hidden `.tmp.driveupload` at 4.4 GB / 9051 files
- 1528 `.py` files outside `.venv`/`__pycache__`/`site-packages`; 108 are `test_*.py`; 23 `pyproject.toml`/`pytest.ini`/`conftest.py`
- 140 archives totalling 639.8 MB; 87 resolve to an extracted folder, 51 were never unpacked here (22 of those contain Python)
- 13 Python scripts exist only inside archives, nowhere in the working tree
- Largest trees: `KnotPlot` 5354 MB, `3D` 2589 MB, `media` 1459 MB, `SST_fermat_pybind_research` 707 MB, `proof-scripts` 488 MB

## 1. `INVENTORY.md` — project overview

- Restate what the repo is, relative to [README.md](c:\workspace\projects\SST-Workbench\README.md) and [WORKBENCH_LAYOUT.md](c:\workspace\projects\SST-Workbench\WORKBENCH_LAYOUT.md), and where those two docs are now out of date (e.g. `to_be_processed/` and `verification-suites/` described as populated; `experiments/` is stubs plus three SYCL `.cpp` files).
- Per-top-level-directory list: size, file count, role, and whether it is code, data, or run output.
- Classify the ~30 root folders into: active research packs, data/asset trees (`KnotPlot`, `media`, `datasets`, `3D`, `generated-figures`), tooling (`scripts`, `templates`, `SST-dashboard`, `GUI`), vendored third-party (`KnotTheory/HFK-Zurich` = Bar-Natan knot Floer homology, Python 2; `KnotTheory/WikiLink` = Java/Mathematica), and relocation stubs (`to_be_processed`, `experiments`).
- Flag the hidden `.tmp.driveupload` (4.4 GB) and the 280 MB `.venv` inside `SST_contact_billiard_hydrodynamic_falsifier_v0.2.0/`.
- Cross-links to the other three inventory docs.

## 2. `INVENTORY_PYTHON.md` — research calculation scripts

Main deliverable. One section per research pack, each stating: purpose, version folders present, which version is live and the evidence, the runnable entry-point scripts with a one-line description of what each computes, test files, and where outputs land.

Order by research theme:

- **Fermat / geodesic**: `SST_fermat_pybind_research` v0.1 to v0.6.1 (live v0.6.1, 30 `run_*.py`, `fermat_ext._fermat_native` pybind11 kernel built via `fermat_ext/build_ext_if_needed.py`)
- **BEM / spectral**: `SST_routeB_RT_bem_research` (v3 to v19; v18 = live production scan, v19 = link parser), `SST_horn_bem_research` (live `sst_horn_neumann_bem_all_audits`), `SST_ssdl_audit_research` (live `ssdl_audit_v0_2`)
- **Constants derivation**: `SST_derive_constants_research/code/` (28 `derive_*`/`solve_*`/`audit_*` gate scripts, `DERIVED_GATE_EVIDENCE_MANIFEST.json`) plus `schrodinger_gate/`
- **Knot / trefoil**: `SST_chi_phase_research` (two lineages: `sst_chi_phase_package_v10B1..v16B0` and `sstcore_chiE_local0..v7`), `SST_Trefoil_Closure`, `SST_ideal_trefoil_biot_research`, `SST21D_knot_order_pipeline` (live v0.2.0, only pack with real pytest config), `SST_Hopf_Benchmark`
- **Falsifiers / predictions**: `SST_dimensionless_dynamic_predictions` (live v0.4.0), `SST_contact_billiard_hydrodynamic_falsifier` (live v0.2.0), `SST_minimal_falsification_harness` (live v0.3.0), `SST_Sutcliffe_HSS_feasibility_gate`, `SST_dark_knot_rayleigh_research`, `SST_Route_I_relative_entropy_PoC` (only `v0.0.4` extracted; the rest of the lineage including the newest `v0.1.0` is zip-only, so cross-reference the archive doc), `SST_v0_8_19_routes_research`
- **Coil / hardware**: `SST_Coil_DigitalTwin_research` (live v10), `SST_CoilLab_research` (live v2_work), `GUI/coils` (18 GUI iterations), `3D/Python`
- **Audits / bridges**: `SST_fs_attachment_audit_research` (25 scripts in `fs_core/`), `SST_contra_swirl_bridge_research` (v0 to v0_6, progressive), `SST_timefield_spectral_v06_research` (output-only, produced by contra-swirl v0_6)
- **Pipelines / legacy**: `KnotPlot/ridgerunner` (25 files, the KnotPlot to ridgerunner tightening pipeline with 11 unit-test files), `KnotPlot/knots`, `proof-scripts`, `datasets/*.py`, `scripts/` (repo reorg helpers), root `sst_gilbert_usability.py`
- Closing section on testing reality: only `SST21D_knot_order_pipeline` and `SST_contact_billiard_hydrodynamic_falsifier` have `[tool.pytest.ini_options]`; everywhere else "tests" are `run_all_checks.py`-style CLI audit batteries; no root-level pytest config.

## 3. `INVENTORY_ARCHIVES.md` — archives as bundles

Organised as **bundles**, not as a flat file list: a zip plus the version-notated folder of the same name are treated as one unit. I already ran the pairing (each zip's stem and its root entry name checked against sibling directories), so the doc reports state per bundle rather than per file.

Three bundle states, with counts already measured:

- **Paired** — zip and its extracted folder both present. 87 of 140 archives resolve to an existing directory (40 of them by exact stem match, the rest via the zip's internal root folder name). These are normal version snapshots; the doc lists them compactly, grouped per research pack.
- **Zip only, never unpacked here** — 51 archives, of which 22 contain Python. Listed in full with size, date, entry count, and internal root names.
- **Folder only, no zip** — version folders with no matching archive, so the snapshot was never made or was left behind elsewhere.

### The section that matters most: code that exists only inside an archive

Cross-checking every `.py` entry inside the 22 orphan zips against all 1528 Python files on disk turned up **13 scripts that exist nowhere in the working tree**:

- `SST_Route_I_relative_entropy_PoC` is the worst case — of 9 archives only `v0.0.4` was ever extracted, so 8 scripts live only in zips: `sst_relative_entropy_route1_poc.py`, `sst_relative_entropy_route1_poc_v0.0.2.py`, `sst_route1_parallel_hierarchy_v0.0.5.py`, `sst_route1_common_foundation_v0.0.6.py`, `sst_route1_nonlinear_adjacency_phase_v0.0.7.py`, `sst_route1_beta_selection_v0.0.8.py`, `legacy_v0_0_7.py`, and `sst_route1_resolved_knot_action_v0.1.0.py` — the last being the newest Route-I work in the whole pack.
- `SST_v0_8_19_..._A_to_D_evidence_pack.zip`: `apply_planck_routes_patch_v0_8_19.py`, `sst_planck_routes_A_to_D_candidate_summary.py`
- `3D\Triple_Gear\Archive\triple_gear_parametric_recovery_phase1.zip`: `triple_gear_parametric_recovery.py`
- `SST_Fseries.zip` and `VAM_Fseries.zip` (both under `proof-scripts/swirl/VAM_PYTHON_SIMULATOINS/`): `vamcore_batch_hypvol_from_fseries.py`

Also record the inverse — orphan zips whose Python is fully mirrored on disk, so nothing is hidden (`bundles\trefoil_closure.zip` 46 files, `SST_Hopf_Python_Scripts_v0.1.zip` 10, the `Sutcliffe` and `routeB/C/D` trial bundles, `knots_for_particles.zip`).

### Remaining content

- Largest archives: `KnotPlot\KnotPlotridgerunner.zip` 176.2 MB, `bundles\trefoil_closure.zip` 37.1 MB, `KnotPlot\ridgerunner\out\out.zip` 36.1 MB, `trefoils.zip` 28.0 MB, `ideal_3_1_1.zip` 27.2 MB.
- Data/results-only orphans (29 archives, no Python): the whole `vortexring-lab-v7.6-release-train` set of 13 package zips, `ideal_3_1_1.zip`, the 6 copies of `pybind11_headers.zip`, and the `datasets` portfolio zips.
- Repeated identical archives: `pybind11_headers.zip` (275801 bytes) 7 times; `batch_runs.zip` (3417213 bytes) twice; `Fresnel_FourierSeries.zip` (296780 bytes) twice; `routeI_heat_guard_patch_bundle_v0_8_19.zip` (181496 bytes) four times.
- `.gitignore` excludes `*.zip`, so none of these 140 archives are in git — the only copy is the local file.

## 4. `INVENTORY_DUPLICATES.md` — nesting and duplication findings

Grouped by kind, each entry giving the paths and the evidence (byte-identical, subset, or differing).

- **Working dir inside working dir**: `SST_minimal_falsification_harness_v0.2.0_Gilbert/SST_minimal_falsification_harness_v0.2.0/`; `Sutcliffe_HSS_feasibility_gate_v0.1.0/Sutcliffe_HSS_feasibility_gate_v0.1.0.zip`; `SST_v0_8_19_.../v3_pack/archive/legacy_extracted_v2_corrected_pack/` (identical SHA-256 to the sibling v2 pack)
- **Older version's output inside newer version dir**: `SST_fermat_pybind_research_v0.6.1/` holding `v0.6.0_campaign_output/`, `v0.6.0_smoke_output/`, `v0.6.0_global_orbit_smoke_output/`
- **Embedded legacy reference copies**: `sst_chi_phase_package_v11B0/legacy_v10B1_reference/`, `v12B0/legacy_v11B0_reference/` (byte-exact); `SST_Coil_DigitalTwin_v10_complete_restored/legacy_all_versions_from_user_zip/` (38 files, identical to v1/v4/v7); `sstcore_chiE_local_v7/exports_previous_*` (3 preserved snapshots)
- **Whole-tree duplication across packs**: `SST_derive_constants_research/code/` vs `SST_routeB_RT_bem_research/outputs/` (28 scripts plus output trees, 66 MB); `Knots_FourierSeries` in three places; `proof-scripts/swirl/VAM_Python_Benchmarks/` vs `Python_Benchmarks/` (19 of 20 byte-identical, differing: `constants.py`, `VAM_Benchmark.py`, `VAM_Benchmark2.py`)
- **Version pairs that are near-identical**: `v0.4.3` vs `v0.4.3_flat` (identical source, `_flat` has no build artifacts); `ssdl_audit` vs `ssdl_audit_v0_2`; `sst_horn_neumann_bem_package` subset of `..._all_audits`; `SST_CoilLab_v1` vs `v2_work` (22 identical paths, plus both carrying export run `run_20260626_232323`); `original_sources/` identical in Coil DigitalTwin v9 and v10
- **Same file in two packs**: `simulate_trefoil_biot_closure.py` byte-identical in `sst_ideal_trefoil_biot_package_v2` and `sstcore_chiE_local_v7`; `test_monopole_from_fseries.py` in `KnotPlot/knots` and `SST_routeB.../knot-data/knotplot`
- **Script copied into its own results dir**: `SST_contra_swirl_bridge_research_v0_4/sst_bridge_v0_4_spectral_epr_results/sst_contra_swirl_bridge_test_v0_4_spectral_epr.py`
- **Duplicate-download artifacts**: `SST_dimensionless_dynamic_predictions_v0.4.0_... (2).zip` (22.7 MB); `compute_Hvortex_and_mass (1).py`; `batch_fseries_vam (1).py`; `sbsL_vam_fit (1).py`; `README (2).md`; `..._audit_(1).md`; `3D/Python` copies (`pythonai.py`, `pythonai - Copy.py`, `Rodin_Coil_6_phases.py` all matching grooved-torus v4)
- **Unresolved merge leftovers**: `SST_Trefoil_Closure/_dashboard_conflict/` (4 files that differ from the root copies); `SST-dashboard/_merge_conflict/exports/ideal.txt`
- **Cross-cutting duplication**: Route-B per-version output dirs existing both inside the version folder and under central `outputs/`; `VAM-lab` vs `VAM-lab2` (5 shared files)
- **Non-source bulk inside packs**: `.tmp.driveupload` (4.4 GB), `SST_contact_billiard_..._v0.2.0/.venv/` (280 MB), `3D/Python/3d_sliced/*.gcode` (60 MB)
- Also note the naming typo `proof-scripts/swirl/VAM_PYTHON_SIMULATOINS/` (which is genuinely distinct content, not a duplicate of `VAM_Python_Benchmarks`) and the missing version numbers in some lineages (Coil DigitalTwin has no v2/v3/v6; contra-swirl has no v0_5).

## Verification

Documentation-only, so no behaviour changes. Sanity-run the two suites that exist at the repo root to confirm nothing was disturbed: `python -m unittest test_sst_gilbert_usability` (4 tests) and `python -m pytest scripts/` (15 tests). Both were passing during research.
