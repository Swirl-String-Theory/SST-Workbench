# Post-SP11 root husk cleanup

Generated: 2026-09-05 (updated same day for full root clean)

Follow-up to [sp11_decommission.md](sp11_decommission.md): empty level-2 scaffolds,
orphan outputs, and remaining root leftovers after junction teardown.

## Actions

| Item | Action |
|------|--------|
| `Katlas_Sources_v0.2.2_Outputs/` | → `03_data/A_knots/03_katlas/v0.2.2/` |
| `KnotInfo/` | → `03_data/A_knots/07_knotinfo/` (7 upstream archives) |
| `SST_Maxwell/*_outputs.zip` (+ `.sha256`) | → `A011-v0.1.0` … `A011-v0.3.1` |
| `SST_Kelvin_Floquet/Kelvin_Joule_*_outputs.zip` (+ `.sha256`) | → `A032-v0.1.0/` |
| Empty husks + `Knot_Library/` + `bundles/` | → `DELETE/<relpath>/` |
| `SST_Trefoil_Closure/` remnant files | → `DELETE/SST_Trefoil_Closure/` |
| Root migration/inventory docs | → `10_docs/migration/` or `10_docs/inventory/root_docs/`; duplicate `INVENTORY_TREE.json` → `DELETE/root_docs/` |
| `falsifiers.md` | → `10_docs/inventory/root_docs/falsifiers.md` |
| `test_sst_gilbert_usability.py` | → `07_scripts/` |
| `SST_routeB_RT_bem_research_outputs.zip.sha256` | → `09_archive/restore/root_zips/` (next to the zip) |
| `KnotPlot/__pycache__/`, root `__pycache__/`, `debug-c30583.log` | deleted |

## Root keepers (intentional)

`README.md`, `falsifier_registry.yaml`, `requirements-workbench.txt`, `pyrightconfig.json`, plus the ten catalog domains and `DELETE/`.

## DELETE retirement

`DELETE/` itself was emptied and removed after the audit in
[delete_retirement.md](delete_retirement.md): Drive duplicates hash-matched catalog
packs, KnotPlot zips matched archive copies, stubs/docs/Trefoil unique scripts were
relocated to `10_docs/migration/` / `A002` / `09_archive/trefoil_closure/root_remnants/`.
