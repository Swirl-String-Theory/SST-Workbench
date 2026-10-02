---
name: SP11 decommission
todos:
  - id: t00
    content: "Soft-retire stubs: `git mv` → `DELETE/<original/relative/path>` (never unlink research)"
    status: completed
  - id: t01
    content: "Stage disposable caches/venvs under `DELETE/` only if reproducible"
    status: completed
  - id: t02
    content: "Remove junctions domain-by-domain after SP10 clean"
    status: completed
  - id: t03
    content: "Archive dedup with hash-matched siblings only; stage candidates to `DELETE/`"
    status: completed
  - id: t04
    content: "Decide `.tmp.driveupload/` separately"
    status: completed
  - id: t05
    content: "Done-criteria: soft-retire complete; junctions gone safely; provenance retained"
    status: completed
---
# SP11 — Decommission

Status: `DONE` · Priority: P4 · Risk: high · Depends on: SP10

## Todos

Progress tracker — checkboxes include completed work so status is obvious at a glance.

- [x] Soft-retire stubs: `git mv` → `DELETE/<original/relative/path>` (never unlink research)
- [x] Stage disposable caches/venvs under `DELETE/` only if reproducible
- [x] Remove junctions domain-by-domain after SP10 clean
- [x] Archive dedup with hash-matched siblings only; stage candidates to `DELETE/`
- [x] Decide `.tmp.driveupload/` separately
- [x] Done-criteria: soft-retire complete; junctions gone safely; provenance retained

**Closed:** Report in `10_docs/migration/sp11_decommission.md`. Stubs soft-retired;
285 junctions + 40 empty scaffolds removed via `os.rmdir` only; caches deferred (no
mass `.venv` wipe); archive staging **0** (safety bar not cleared); `.tmp.driveupload/`
absent. Provenance CSVs retained. `07_scripts` tests green after SP11 (legacy-path
assumptions updated; bootstrap no longer recreates junctions on the live tree).

## Soft-delete via `DELETE/`

Any former delete candidate is relocated with `git mv` to `DELETE/<path relative to repo root>`,
preserving the original folder layout. No `git rm`, no filesystem unlink of research or stub content.

The only sub-plan that soft-retires paths. **Nothing is unlinked.** It runs **only after SP10 passes**, and it is ordered so
that each deletion is smaller in consequence than the one after it.

Risk is marked high not because the steps are difficult but because they are irreversible in a way
nothing before them was. Every prior phase could be undone with `git mv` and a junction removal.

## Order, and why

### 1. Relocation stubs — done

| Path | Contents |
|------|----------|
| `to_be_processed/` | one relocation `README.md` → `DELETE/to_be_processed/` |
| `experiments/derive_constants/` | stub README → `DELETE/experiments/derive_constants/` |
| `experiments/trefoil/` | stub tree → `DELETE/experiments/trefoil/` |
| `falsifier_registry/` | README → `DELETE/falsifier_registry/` (`falsifier_registry.yaml` stays) |

Executed with `python 07_scripts/move_phase.py --phase SP11 --apply` then `--verify`.

### 2. Build and cache residue — deferred (documented)

`.venv/` counts under `01_research/`: 96. `run_01_install.cmd`: 4.
Precondition for staging (recreate via install) not met for most families — no mass move.

### 3. Junction layer removal — done

Preconditions met (SP10: 0 fail). Helper: `07_scripts/sp11_decommission.py remove-junctions`.

- Snapshot: `junction_registry_pre_sp11.csv`
- Live junctions removed: **285** (`os.rmdir` on reparse points)
- Empty level-2 scaffolds removed: **40**
- Already gone: **20**
- Errors: **0**
- Live root junctions remaining: **0**

Registry CSV kept as provenance (not wiped). Restore path:
`07_scripts/bootstrap_junctions.cmd`.

### 4. Archive deduplication — complete with zero staging

Safety API: `archive_zip_safe_to_stage` (every zip member must hash-match an extracted
counterpart). No zip cleared the bar; **0** staged to `DELETE/`. Written record in
`sp11_decommission.md`.

### 5. Old generated outputs

Left in place / already gitignored. Not mass-staged.

### 6. `.tmp.driveupload/` — absent

Not on disk. Outside migration; no action.

## What is explicitly not deleted

Restating the non-goals, because this is the phase where they are most tempting to violate:

- **Old versions are not deleted** because git keeps them. Git keeping a file is not the same as a
  reproducible research pack being available. The version directories stay under catalog paths.
- **Archives are not re-extracted.**
- **Blind and revealed artifacts are not merged.**
- **Outputs are not consolidated into one global directory.**
- **Old identifiers are not rewritten.** They live on in `legacy_paths`, `legacy_dir` and
  `path_map.csv` permanently.

## Tests written

- `test_no_stubs.py`
- `test_junction_removal_safe.py`
- `test_archive_dedup_safety.py`
- `test_break_set_empty.py`

`test_level2_junctions.py` skips when the compat layer is gone (post-SP11).

## Rollback

Sections 1 and 2 are recoverable from git or by re-running installers. Section 3 is recoverable by
re-running `bootstrap_junctions.cmd`, as long as `junction_registry.csv` /
`junction_registry_pre_sp11.csv` and `path_map.csv` are intact.

Sections 4 and 5 remain **not** recoverably unlinked — and we staged nothing there.

## Done criteria

- [x] Stubs gone; `INVENTORY_TREE.json` regenerated; report accurate
- [x] Junction layer removed safely; suite green
- [x] Archive dedup recorded (0 staged; safety evidence in tests + report)
- [x] `10_docs/migration/` retains `path_map.csv`, `checksums.sha256`,
  `junction_registry.csv`, `junction_registry_pre_sp11.csv`, gate report
- [x] Final tree statistics recorded in `sp11_decommission.md`
