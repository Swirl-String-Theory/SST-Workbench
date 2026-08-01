# MOVE derive_constants -> research folders

- Source: `experiments/derive_constants/` (baseline files: **8831**)
- Script: `scripts/reorg_derive_constants.py` (two-pass: primary + resume)
- Run logs: `scripts/reorg_derive_constants_run.log`, `scripts/reorg_derive_constants_run2.log`
- Dropped stubs: `_mounttest.txt`, `_patch.py`, `_patch2.py`, `_tmp_head.py` (4)
- Regenerable `__pycache__` `.pyc` removed during locked-dir cleanup (~13)
- Final destination files: **8814** (+ stub `experiments/derive_constants/README.md`)

## Destinations

| Destination | Files |
|-------------|------:|
| `SST_derive_constants_research/` | 582 |
| `SST_routeB_RT_bem_research/` | 7263 |
| `SST_Coil_DigitalTwin_research/` | 460 |
| `SST_CoilLab_research/` | 237 |
| `SST_contra_swirl_bridge_research/` | 37 |
| `SST_fs_attachment_audit_research/` | 164 |
| `SST_timefield_spectral_v06_research/` | 71 |
| **Total** | **8814** |

## Layout notes

- RouteB versions: `SST_routeB_RT_bem_research_v3` … `_v19`, plus `_v3_1`/`_v3_2`/`_v3_3`, `stecklov`
- Matching `outputs_routeB_BEM_v*` live inside the version folder; non-matching under `outputs/legacy/`
- CoilLab / Coil DigitalTwin keep their existing version folder names
- Micropacks: emergent-SR + Schrödinger → derive; hopfion/writhe + STLs → fs/attachment; CASTLE `externe_data` → timefield
- Archive conflict-loser left as `archive/sstcore-derive.zip` (not relocated)

## Stub

`experiments/derive_constants/README.md` points at the seven research roots above.
