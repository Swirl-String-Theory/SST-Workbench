# DELETE folder retirement audit

Generated: 2026-09-05

Goal: empty and remove `DELETE/` only after every item was proven redundant,
relocated to a catalog/archive home, or preserved as migration documentation.

## Verdicts

| DELETE item | Evidence | Action |
|-------------|----------|--------|
| `Katlas_Source_Crawler_v0.2.2 (1)/` | 31/31 files hash-match `04_tools/.../B001-v0.2.2` | removed (Drive duplicate) |
| `PTSA_..._v1.0.0 (1)/` | 56/56 hash-match `E009-v1.0.0` | removed (Drive duplicate) |
| `SST_Katlas_Link_Geometry_Conditioning_v2.0.0 (1)/` | 20/20 hash-match `E008-v2.0.0` | removed (Drive duplicate) |
| `KnotPlot/*_outputs.zip` | hash-match `09_archive/restore/KnotPlot/` | removed |
| Stub READMEs | pointers only; content kept | → `10_docs/migration/retired_stubs/` |
| `Knot_Library/README.md` + `_setup_provenance.py` | not previously under A002 | → `02_libraries/.../A002_knot_library/` |
| `SST_Trefoil_Closure/` unique scripts | not in catalog homes | → `09_archive/trefoil_closure/root_remnants/` |
| `SST_Trefoil_Closure/build` + `.pyd/.obj` | rebuildable binaries | discarded |
| `root_docs/INVENTORY_TREE.json` | differs from live inventory | → `10_docs/migration/snapshots/` |

## Result

`DELETE/` directory removed from the working tree. Historical destinations remain
recorded in `path_map.csv` (rows with `new_path` under `DELETE/` stay as provenance).

## Tests

- `test_no_stubs.py` — stubs absent at root; retired READMEs under migration docs; no `DELETE/`
- `test_no_empty_root_husks.py` — Knot_Library docs under A002; root cleanliness without `DELETE/`
