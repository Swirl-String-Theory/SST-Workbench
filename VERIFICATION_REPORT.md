# Migration verification report (rev. 5)

Date: 2026-07-03

## Derive_Constants merge integrity

| Metric | Value |
|--------|------:|
| Swirl baseline files | 8828 |
| SSTcore baseline files | 8540 |
| Expected total | 17368 |
| Workbench `experiments/derive_constants/` | 8978 |
| `archive/conflict-losers/` | 8390 |
| **Sum** | **17368** ✓ |

## Frozen paths (unchanged)

| Path | Files |
|------|------:|
| `SwirlStringTheory/papers/VAM/` | 1552 ✓ |

## Source paths removed (move-only)

| Path | Status |
|------|--------|
| `papers/SST-CANON/Derive_Constants/` | Gone from source ✓ |
| `SwirlStringTheory/SST_Dashboard/` | Gone ✓ |
| `SwirlStringTheory/code/` | Gone ✓ |
| `SSTcore/SST_Dashboard/` | Gone ✓ |
| `SSTcore/examples/` | Gone ✓ |

## BEM structure

`experiments/derive_constants/bem/` contains `coillab/`, `outputs/`, `demos/`, `knot-data/`, `root/`.

## Conflict log

See [CONFLICT_RESOLUTION.md](CONFLICT_RESOLUTION.md) (~8390 SSTcore duplicate entries; Swirl canonical default).

## Agent constraints honored

- No git commits or pushes
- No file deletion (losers archived)
- `papers/VAM/`, `tools/`, `out/` not moved
