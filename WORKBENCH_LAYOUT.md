# SST-Workbench layout

## Canonical Derive_Constants (relocated)

Primary source (moved from):

`SwirlStringTheory/papers/SST-CANON/Derive_Constants/`

→ `experiments/derive_constants/` (historical merge target)

→ **split** into Workbench-root research folders (fermat-style; see
`MOVE_DERIVE_CONSTANTS_MANIFEST.md`):

| Research root | Contents |
|---------------|----------|
| `SST_derive_constants_research/` | Manuscripts, gate scripts, non-routeB `outputs_*`, emergent-SR / Schrödinger micropacks |
| `SST_routeB_RT_bem_research/` | Versioned `SST_routeB_RT_bem_research_v*`, demos, knot-data, legacy outputs |
| `SST_Coil_DigitalTwin_research/` | `SST_Coil_DigitalTwin_v*` + exports |
| `SST_CoilLab_research/` | `SST_CoilLab_v1`, `SST_CoilLab_v2_work` |
| `SST_contra_swirl_bridge_research/` | Bridge scripts + `sst_bridge_*` results |
| `SST_fs_attachment_audit_research/` | `fs_core`, attachment audits, hopfion/writhe, geometry STLs |
| `SST_timefield_spectral_v06_research/` | Spectral/timefield v06 artifacts + CASTLE `externe_data` |

Stub pointer: `experiments/derive_constants/README.md`

SSTcore merge losers are archived as `archive/sstcore-derive.zip`
(see `CONFLICT_RESOLUTION.md`).

## BEM (now under `SST_routeB_RT_bem_research/`)

| Subfolder | Source pattern |
|-----------|----------------|
| `SST_routeB_RT_bem_research_v*/` | `routeB_RT_bem_v*` scripts + matching `outputs_routeB_BEM_v*` |
| `demos/` | `demo/`, `demo_fastv*` |
| `knot-data/` | `knotplot/`, `Knots_FourierSeries/`, ideal/knots helpers |
| `outputs/legacy/` | `outputs_routeB_SSTcore_*`, `outputs_routeB_correct_*`, demos |
| `shared/` | scale-role helpers, run_*.sh |

## Trefoil closure (relocated)

Merged to Workbench root `SST_Trefoil_Closure/`:

1. Nested trees: `experiments/trefoil/closure/{sstcore,swirl}/trefoil_closure/`
2. Dashboard leftovers: `experiments/trefoil/closure/{sstcore,swirl}/` (swirl ⊆ sstcore)

Path conflicts vs already-merged nested files are kept under
`SST_Trefoil_Closure/_dashboard_conflict/`.

Stub: `experiments/trefoil/closure/README.md`.

## GUI dashboards

| Path | Origin |
|------|--------|
| `SST-dashboard/` | Union of former `SSTcore/SST_Dashboard/` and `SwirlStringTheory/SST_Dashboard/` (flattened; was `SST-dashboard/{sstcore,swirl}/`) |

Sole merge conflict parked at `SST-dashboard/_merge_conflict/exports/ideal.txt` (canonical `exports/ideal.txt` from sstcore).

## Former `to_be_processed/` (relocated)

| Research root | Contents |
|---------------|----------|
| `SST_chi_phase_research/` | chi-phase package v10–v16 + `sstcore_chiE_local*` |
| `SST_horn_bem_research/` | horn Dirichlet/Neumann BEM packs |
| `SST_v0_8_19_routes_research/` | Planck Routes / RouteA / nonfit / torsion packs |
| `SST_ssdl_audit_research/` | `ssdl_audit`, `ssdl_audit_v0_2` |
| `SST_dark_knot_rayleigh_research/` | dark-knot Rayleigh harness |
| `SST_ideal_trefoil_biot_research/` | biot package v2, trefoil BS, 3d collider robust |
| `SST_fermat_pybind_research/…_v0.1/` | absorbed fermat v0.1 |
| `SST_Route_I_relative_entropy_PoC/routeI_heat_guard_…/` | Route-I heat-guard patch |
| `GUI/vortexring-lab/inbox_from_to_be_processed/` | vortexring/gem HTML+JS+builders |

Stub: `to_be_processed/README.md`.

## Proof scripts

| Path | Origin |
|------|--------|
| `proof-scripts/sstcore/examples/` | Research subset only (helicity, braid, investigate, taichi, …) — **API examples restored to SSTcore** |
| `proof-scripts/swirl/` | `SwirlStringTheory/code/` (incl. VAM Python simulators) |
| `proof-scripts/SSTcore_full_probe.py` | SwirlStringTheory root |

### Restored to SSTcore (not in Workbench)

Release/API examples live again in `SSTcore/examples/` (`example_*.py`, `node_examples/`, helpers).

## Verification & experiments (from SSTcore/docs)

| Path | Origin |
|------|--------|
| `verification-suites/embedded-knots/test_embedded_knots.py` | `SSTcore/docs/test_embedded_knots.py` |
| `experiments/sycl/` | `SSTcore/docs/*.cpp` SYCL probes |

## Frozen in SwirlStringTheory (not moved)

- `papers/VAM/**`
- `papers/SST-CANON/**` except former `Derive_Constants/`
- All `papers/SST-NN_*/`
- `tools/**`, `out/**`

Evidence pack scripts remain at:
`papers/SST-CANON/SST_v0_8_12_evidence_pack/scripts/`

## Datasets & media

| Path | Origin |
|------|--------|
| `datasets/` | `SwirlStringTheory/data/` |
| `datasets/resources-swirl/` | `SwirlStringTheory/resources/` |
| `generated-figures/resources-results/` | `SSTcore/resources/Results/` |
| `media/images/` | `SwirlStringTheory/docs/images/` |
| `media/presentations/` | `SwirlStringTheory/docs/Presentation_PDF/` |
| `media/audio-voiceovers/` | `SSTcore/docs/Generate_Audio_Voiceovers/` |
| `hardware/3d-prints/` | `SwirlStringTheory/3d-prints/` |
| `archive/swirl/` | `SwirlStringTheory/archive/` |
| `bundles/trefoil_closure.zip` | SwirlStringTheory root |
