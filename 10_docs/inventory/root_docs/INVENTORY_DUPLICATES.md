# SST-Workbench — nesting and duplication findings

Companion to [INVENTORY.md](INVENTORY.md). Snapshot: **2026-08-04**.

Findings only — **no cleanup recommendations**. Evidence: path layout, byte identity
where checked in research, or “subset / near-identical” by file-name overlap.

---

## 1. Working directory inside working directory

| Path | What happened |
|------|----------------|
| `SST_minimal_falsification_harness/SST_minimal_falsification_harness_v0.2.0_Gilbert/SST_minimal_falsification_harness_v0.2.0/` | Wrapper folder contains an inner folder matching the zip root name — classic unpack-into-parent pattern. Gilbert BATs / calibration live only in the **inner** folder. |
| `SST_Sutcliffe_HSS_feasibility_gate/Sutcliffe_HSS_feasibility_gate_v0.1.0/Sutcliffe_HSS_feasibility_gate_v0.1.0.zip` | Zip sits **inside** its own extracted tree (19 entries; Python fully mirrored on disk). |
| `SST_v0_8_19_routes_research/…_v3_preregistered_all_inclusive_pack/archive/legacy_extracted_v2_corrected_pack/` | Extracted duplicate of sibling pack `…_A_to_D_equivalence_corrected_pack/`; `scripts/route_ABCD_equivalence_scan_audit.py` has **identical SHA-256** to the live v2 copy. |

---

## 2. Older version’s output inside a newer version directory

| Location | Leftover dirs |
|----------|---------------|
| `SST_fermat_pybind_research/SST_fermat_pybind_research_v0.6.1/` | `v0.6.0_campaign_output/`, `v0.6.0_smoke_output/`, `v0.6.0_global_orbit_smoke_output/` alongside `v0.6.1_*` outputs |

Campaign artifacts from runs performed on / carried into the v0.6.1 tree — not nested source packages.

---

## 3. Embedded legacy reference copies

| Copy | Relationship |
|------|----------------|
| `SST_chi_phase_research/sst_chi_phase_package_v11B0/legacy_v10B1_reference/` | **Exact duplicate** of the two `.py` files in `…_v10B1/` (SHA256 match); lacks README/exports |
| `SST_chi_phase_research/sst_chi_phase_package_v12B0/legacy_v11B0_reference/` | **Exact duplicate** of the two `.py` files in `…_v11B0/` |
| `SST_Coil_DigitalTwin_research/SST_Coil_DigitalTwin_v10_complete_restored/legacy_all_versions_from_user_zip/` | 38 `.py` archive of user zip; sampled files **byte-identical** to sibling `v1` / `v4` / `v7` modules; not a runnable tree |
| `SST_chi_phase_research/sstcore_chiE_local_v7/exports_previous_*` | Three preserved export snapshots from the v6→v7 merge |

---

## 4. Whole-tree duplication across packs

| Pair | Evidence |
|------|----------|
| `SST_derive_constants_research/code/` ↔ `SST_routeB_RT_bem_research/outputs/` | 28 identically named gate scripts; matching `outputs_*` trees (~66 MB under Route-B `outputs/`). Prefer derive-constants as manuscript-linked home. |
| `KnotPlot/Knots_FourierSeries/` ↔ `SST_routeB_RT_bem_research/knot-data/Knots_FourierSeries/` | 40 identical subdirectory names; sample `3_1/knot.3_1.fseries` **byte-identical** |
| Also vs `proof-scripts/swirl/SST_Mathematical_Proof_Python/Knots_FourierSeries/` | Same catalog pattern (third copy) |
| `proof-scripts/swirl/VAM_Python_Benchmarks/` ↔ `…/SST_Mathematical_Proof_Python/Python_Benchmarks/` | **19 of 20** comparable files byte-identical; differ: `constants.py`, `VAM_Benchmark.py`, `VAM_Benchmark2.py`. Extra only in VAM_Python_Benchmarks: `Sonoluminescence/sbsL_vam_fit (1).py` |

**Not duplicates (separate lineages):**

| Pair | Note |
|------|------|
| `SST_Trefoil_Closure/sst_chi_phase_package*` (v1–v6) vs `SST_chi_phase_research/sst_chi_phase_package_v*` (v10B1–v16B0) | Different version schemes and physics stages |
| `proof-scripts/…/VAM_PYTHON_SIMULATOINS/` vs `VAM_Python_Benchmarks/` | Typo folder name; **distinct** simulator/QC content (not a benchmarks copy) |

---

## 5. Near-identical version pairs

| Pair | Relationship |
|------|----------------|
| `SST_fermat_…_v0.4.3` vs `…_v0.4.3_flat` | Identical 47 source files; `_flat` has no `build/`, `.pyd`, or smoke outputs (113 vs 47 files on disk) |
| `ssdl_audit/` vs `ssdl_audit_v0_2/` | Near-identical package layout; v0_2 adds pyproject, README, CHANGELOG, result JSON |
| `sst_horn_neumann_bem_package/` vs `sst_horn_neumann_bem_all_audits/` | Package is a **subset** of all_audits (shared core + sweep; audits only in all_audits) |
| `SST_CoilLab_v1` vs `SST_CoilLab_v2_work` | 22 identical relative paths; v2 adds mutual-inductance modules; both contain export run `run_20260626_232323` |
| Coil DigitalTwin `v9_complete/original_sources/` vs `v10_…/original_sources/` | All 4 files **byte-identical** (`GUI-SawBowl.py`, rodin guides, …) |

Missing version numbers in lineages (gaps, not duplicates): Coil DigitalTwin has no v2/v3/v6; contra-swirl has no v0_5 folder (v0_6 docstring references “v0.5” as prior work).

---

## 6. Same file in two packs

| File | Locations |
|------|-----------|
| `simulate_trefoil_biot_closure.py` | `SST_ideal_trefoil_biot_research/…_v2/` and `SST_chi_phase_research/sstcore_chiE_local_v7/` — **byte-identical** (7963 bytes) |
| `test_monopole_from_fseries.py` | `KnotPlot/knots/` and `SST_routeB_RT_bem_research/knot-data/knotplot/` |
| Helicity / knot GUIs | `proof-scripts/sstcore/examples/` and `…/Python_Computations/py_knots/` (same basenames); `GUI-biot-savart_COIL sim.py` and `GUI - quarck streamlines.py` identical between `SST_Mathematical_Proof_Python/` and `VAM_PYTHON_SIMULATOINS/` |
| `build_knotplot_knots_data.py` / `knotplot_knots_data.js` | Both `KnotPlot/` and `GUI/vortexring-lab/` |

---

## 7. Script copied into its own results directory

| Path |
|------|
| `SST_contra_swirl_bridge_research/SST_contra_swirl_bridge_research_v0_4/sst_bridge_v0_4_spectral_epr_results/sst_contra_swirl_bridge_test_v0_4_spectral_epr.py` |

Copy of the runner sitting inside the results folder it produces.

---

## 8. Duplicate-download / “ (1)” / “ (2)” artifacts

| Path | Note |
|------|------|
| `SST_dimensionless_dynamic_predictions/…_v0.4.0_iso_gamma_area_dynamic_clock (2).zip` | 22.7 MB second archive beside stem zip |
| `proof-scripts/…/VAM_PYTHON_SIMULATOINS/compute_Hvortex_and_mass (1).py` | Duplicate download suffix |
| `proof-scripts/…/VAM_PYTHON_SIMULATOINS/fseries/batch_fseries_vam (1).py` | Same |
| `proof-scripts/…/VAM_Python_Benchmarks/Sonoluminescence/sbsL_vam_fit (1).py` | Same |
| `SST_dark_knot_rayleigh_research/…/README (2).md` | Accidental README duplicate |
| `SST_derive_constants_research/audits/emergent_SR/…_audit_(1).md` | Near-duplicate markdown audits |
| `3D/Python/pythonai.py`, `pythonai - Copy.py`, `Rodin_Coil_6_phases.py` | Match grooved-torus v4 header / content |
| `3D/Python/…_v5_mirrored_handedness.py` and `…(1).py` | Duplicate filename pair |

---

## 9. Unresolved merge leftovers

| Path | Note |
|------|------|
| `SST_Trefoil_Closure/_dashboard_conflict/` | Staging copies of `main.py`, `main_gui.py`, master sweep, GUI v9_3 — **hash differs** from root copies |
| `SST-dashboard/_merge_conflict/exports/ideal.txt` | Conflict parked during dashboard flatten; canonical `exports/ideal.txt` from sstcore side |

---

## 10. Cross-cutting / structural duplication

| Pattern | Detail |
|---------|--------|
| Route-B outputs in two places | Per-version dirs under `SST_routeB_RT_bem_research_v14/` **and** under central `outputs/outputs_routeB_BEM_v14_stage*` |
| `VAM-lab` vs `VAM-lab2` | Both under `VAM_PYTHON_SIMULATOINS/`; 5 shared `.py` files; lab2-only `generate_data.py` |
| CoilLab `original_sources/` | Identical 4-file set in v1 and v2_work |
| VortexRing Lab archives | `GUI/vortexring-lab/vortexring-lab-v7.6-release-train/` (13 package zips); `archive/v7-tools/`; `inbox_from_to_be_processed/` (staging); parallel modular tree `GUI/vortexlab-modular-v7.6.25b-m1/` |
| `media/images/images/` | Nested `images` under `images` (same-name nesting) |

---

## 11. Non-source bulk inside packs

| Location | Size | Nature |
|----------|-----:|--------|
| `.tmp.driveupload/` | 4.4 GB / 9051 files | Hidden Google Drive sync staging |
| `SST_contact_billiard_hydrodynamic_falsifier/…_v0.2.0/.venv/` | ~280 MB | Virtualenv inside research pack |
| `3D/Python/3d_sliced/*.gcode` | ~60 MB | Slicer output |
| `KnotPlot/ridgerunner/out/` | ~3.91 GB | RR campaign outputs |
| `KnotPlot/knots/` | ~1.08 GB | Per-candidate build / RR trees |

---

## 12. Naming note (not a duplicate)

`proof-scripts/swirl/VAM_PYTHON_SIMULATOINS/` — spelling typo (“SIMULATOINS”). Content is
simulators / QC / VAM-lab / inference, **not** a second copy of `VAM_Python_Benchmarks/`.

---

## Cross-reference

- Archives that were never unpacked, and scripts only inside zips:
  [INVENTORY_ARCHIVES.md](INVENTORY_ARCHIVES.md)
- Which version is live for each research pack:
  [INVENTORY_PYTHON.md](INVENTORY_PYTHON.md)
- Top-level size map:
  [INVENTORY.md](INVENTORY.md)
