# SP11 decommission

Generated: 2026-09-05T09:45:44Z

## Stubs

Soft-retired via `git mv` to `DELETE/<original/relative/path>`.

| original | DELETE path |
|----------|-------------|
| `to_be_processed/` | `DELETE/to_be_processed/` |
| `falsifier_registry/` | `DELETE/falsifier_registry/` |
| `experiments/derive_constants/` | `DELETE/experiments/derive_constants/` |
| `experiments/trefoil/` | `DELETE/experiments/trefoil/` |

## Caches / `.venv`

- `.venv` directories under `01_research/`: **159**
- `run_01_install.cmd` files under `01_research/`: **4**
- **Decision:** deferred. A `.venv` is disposable only when install can
  recreate it; most families lack `run_01_install.cmd`. No mass staging.

## Junctions

- junctions removed: **280**
- empty scaffolds removed: **40**
- already gone: **25**
- nonempty scaffolds skipped: **0**
- errors: **0**
- live root junctions remaining: **0**
- Provenance retained: `10_docs/migration/junction_registry.csv` and
  `junction_registry_pre_sp11.csv` (snapshot before teardown).
- Restore: `07_scripts/bootstrap_junctions.cmd` (rebuilds from path_map).
  **Warning:** a live-tree bootstrap recreates all junctions — do not run it
  unless intentional. SP11 fixed `test_bootstrap.py` so pytest no longer does that.

## Archive deduplication

- **Decision:** zero zips staged to `DELETE/`.
- Reason: `INVENTORY_ARCHIVES.md` still lists scripts that exist only
  inside archives; SP11 only stages a zip when every member has a
  hash-matching extracted counterpart (`archive_zip_safe_to_stage`).
- No zip cleared that bar in this pass; archives stay under
  `09_archive/restore/` (junction target).

## `.tmp.driveupload/`

- **Absent** on disk — no action. Outside migration scope.

## Provenance (kept forever)

- `10_docs/migration/path_map.csv`
- `10_docs/migration/checksums.sha256`
- `10_docs/migration/junction_registry.csv`
- `10_docs/migration/junction_registry_pre_sp11.csv`
- `10_docs/migration/reproducibility_gate.md`

