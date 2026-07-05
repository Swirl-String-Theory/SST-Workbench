# SST-Workbench layout

## Canonical Derive_Constants

Primary source (moved from):

`SwirlStringTheory/papers/SST-CANON/Derive_Constants/`

→ `experiments/derive_constants/`

SSTcore `SST_Dashboard/Derive_Constants/` was merged with conflict rules; SSTcore
duplicates are in `archive/conflict-losers/sstcore-derive/` unless SSTcore was
≥30 days newer (see `CONFLICT_RESOLUTION.md`).

## BEM (`experiments/derive_constants/bem/`)

| Subfolder | Source pattern |
|-----------|----------------|
| `coillab/` | `SST_CoilLab_v*` |
| `outputs/` | `outputs_routeB_BEM_v*`, `outputs_v*`, `outputs_routeB_*`, `demo_outputs_*` |
| `demos/` | `demo/`, `demo_fastv*` |
| `knot-data/` | `knotplot/`, `Knots_FourierSeries/` |
| `root/` | Remaining routeB scripts and CSV at routeB root |

## GUI dashboards

| Path | Origin |
|------|--------|
| `gui/dashboard/sstcore/` | `SSTcore/SST_Dashboard/` (minus merged Derive_Constants) |
| `gui/dashboard/swirl/` | `SwirlStringTheory/SST_Dashboard/` |

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
