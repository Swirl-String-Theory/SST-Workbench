# Migration manifest (rev. 5)

Generated during SST-Workbench migration. **Move-only** — no file deletion.

## Baseline file counts

| Path | Files |
|------|------:|
| SwirlStringTheory/papers/SST-CANON/Derive_Constants | 8828 |
| SSTcore/SST_Dashboard/Derive_Constants | 8540 |
| SwirlStringTheory/papers/VAM (FROZEN) | 1552 |

## Action legend

| Action | Meaning |
|--------|---------|
| MOVE | Whole tree relocated to Workbench |
| MERGE | SSTcore Derive_Constants merged with conflict rules |
| FROZEN | Must remain untouched in source repo |

## SwirlStringTheory → SST-Workbench

| source_path | workbench_path | action |
|-------------|----------------|--------|
| papers/SST-CANON/Derive_Constants/ | experiments/derive_constants/ | MOVE |
| SST_Dashboard/ | gui/dashboard/swirl/ | MOVE |
| code/ | proof-scripts/swirl/ | MOVE |
| data/ | datasets/ | MOVE |
| resources/ | datasets/resources-swirl/ | MOVE |
| 3d-prints/ | hardware/3d-prints/ | MOVE |
| archive/ | archive/swirl/ | MOVE |
| docs/images/ | media/images/ | MOVE |
| docs/Presentation_PDF/ | media/presentations/ | MOVE |
| trefoil_closure.zip | bundles/trefoil_closure.zip | MOVE |
| SSTcore_full_probe.py | proof-scripts/SSTcore_full_probe.py | MOVE |

## FROZEN (SwirlStringTheory)

| source_path | action |
|-------------|--------|
| papers/VAM/** | FROZEN |
| papers/** (except Derive_Constants) | FROZEN |
| tools/** | FROZEN |
| out/** | FROZEN |

## SSTcore → SST-Workbench

| source_path | workbench_path | action |
|-------------|----------------|--------|
| SST_Dashboard/Derive_Constants/ | experiments/derive_constants/ | MERGE |
| SST_Dashboard/ (remainder) | gui/dashboard/sstcore/ | MOVE |
| examples/ | proof-scripts/sstcore/examples/ | MOVE |
| resources/Results/ | generated-figures/resources-results/ | MOVE |
| docs/Generate_Audio_Voiceovers/ | media/audio-voiceovers/ | MOVE |

## Conflict rules (Derive_Constants MERGE)

- Default winner: Swirl (canonical)
- SSTcore wins if LastWriteTime ≥ 30 days newer
- Loser → archive/conflict-losers/sstcore-derive/

---

## Addendum: RESTORE (examples terug naar SSTcore)

| source (Workbench) | destination (SSTcore) | action |
|--------------------|----------------------|--------|
| proof-scripts/sstcore/examples/example_*.py (19) | examples/ | RESTORE |
| proof-scripts/sstcore/examples/{helpers,trefoil*,…} | examples/ | RESTORE |
| proof-scripts/sstcore/examples/node_examples/ | examples/node_examples/ | RESTORE |
| proof-scripts/sstcore/examples/{helicity,braid,investigate,…} | *(stay Workbench)* | KEEP |

## Addendum: SSTcore/docs extract

| source (SSTcore/docs) | destination (Workbench) | action |
|-----------------------|-------------------------|--------|
| main_sycl.cpp, list_sycl_devices.cpp, vec_add.cpp | experiments/sycl/ | MOVE |
| test_embedded_knots.py | verification-suites/embedded-knots/ | MOVE |
| build_wheels_*.{py,ps1,bat,sh} | SSTcore/scripts/ | RELOCATE (not Workbench) |

## Addendum: derive_constants → fermat-style research roots

| source (Workbench) | destination | action |
|--------------------|-------------|--------|
| experiments/derive_constants/ (post-merge tree) | `SST_derive_constants_research/`, `SST_routeB_RT_bem_research/`, `SST_Coil_DigitalTwin_research/`, `SST_CoilLab_research/`, `SST_contra_swirl_bridge_research/`, `SST_fs_attachment_audit_research/`, `SST_timefield_spectral_v06_research/` | MOVE (split) |
| archive/conflict-losers/sstcore-derive/ | archive/sstcore-derive.zip | ZIP (user) |

Details: `MOVE_DERIVE_CONSTANTS_MANIFEST.md`. Script: `scripts/reorg_derive_constants.py`.

## Addendum: trefoil_closure → SST_Trefoil_Closure

| source (Workbench) | destination | action |
|--------------------|-------------|--------|
| experiments/trefoil/closure/swirl/trefoil_closure/ | SST_Trefoil_Closure/ | MOVE |
| experiments/trefoil/closure/sstcore/trefoil_closure/ (sstcore-only paths) | SST_Trefoil_Closure/ | UNION MOVE |
| experiments/trefoil/closure/{sstcore,swirl}/trefoil_closure/ | stub README only | REPLACE |

Script: `scripts/merge_trefoil_closure.py`.

## Addendum: closure sstcore/swirl → SST_Trefoil_Closure

| source (Workbench) | destination | action |
|--------------------|-------------|--------|
| experiments/trefoil/closure/sstcore/ (excl. stub trefoil_closure) | SST_Trefoil_Closure/ | UNION MOVE |
| experiments/trefoil/closure/swirl/ | *(subset of sstcore; removed)* | DROP after verify |
| conflicting paths | SST_Trefoil_Closure/_dashboard_conflict/ | MOVE |
| experiments/trefoil/closure/ | stub README only | REPLACE |

Script: `scripts/merge_closure_sstcore_swirl.py`.

## Addendum: SST-dashboard sstcore/swirl flatten

| source (Workbench) | destination | action |
|--------------------|-------------|--------|
| SST-dashboard/swirl/ | SST-dashboard/ | MOVE (first) |
| SST-dashboard/sstcore/ | SST-dashboard/ | UNION MOVE |
| SST-dashboard/exports/ideal.txt (swirl) | SST-dashboard/_merge_conflict/exports/ideal.txt | CONFLICT park |
| SST-dashboard/{sstcore,swirl}/ | *(removed)* | DROP |

Script: `scripts/merge_sst_dashboard.py`.

## Addendum: to_be_processed → research roots

| source (Workbench) | destination | action |
|--------------------|-------------|--------|
| to_be_processed/chi_phase/* | SST_chi_phase_research/ | MOVE |
| to_be_processed/sst_horn_* | SST_horn_bem_research/ | MOVE |
| to_be_processed/SST_v0_8_19_* + nonfit/torsion | SST_v0_8_19_routes_research/ | MOVE |
| to_be_processed/ssdl_audit* | SST_ssdl_audit_research/ | MOVE |
| to_be_processed/SST_dark_knot_rayleigh_harness | SST_dark_knot_rayleigh_research/ | MOVE |
| to_be_processed/sst_ideal_trefoil_biot* / sst_trefoil_bs / sst_3d_collider_robust | SST_ideal_trefoil_biot_research/ | MOVE |
| to_be_processed/SST_fermat_pybind_research_v0.1 | SST_fermat_pybind_research/…_v0.1/ | MOVE |
| to_be_processed/routeI_heat_guard_patch_bundle_v0_8_19 | SST_Route_I_relative_entropy_PoC/ | MOVE |
| to_be_processed/*.{html,js,md,py,txt} (loose) | GUI/vortexring-lab/inbox_from_to_be_processed/ | MOVE |
| to_be_processed/ | stub README only | REPLACE |

Script: `scripts/reorg_to_be_processed.py`.
