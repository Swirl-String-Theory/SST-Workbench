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
