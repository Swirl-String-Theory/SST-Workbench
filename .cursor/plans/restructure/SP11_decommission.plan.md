# SP11 — Decommission

Status: `PLANNED` · Priority: P4 · Risk: high · Depends on: SP10

The only sub-plan that deletes anything. It runs **only after SP10 passes**, and it is ordered so
that each deletion is smaller in consequence than the one after it.

Risk is marked high not because the steps are difficult but because they are irreversible in a way
nothing before them was. Every prior phase could be undone with `git mv` and a junction removal.

## Order, and why

### 1. Relocation stubs — zero risk

| Path | Contents |
|------|----------|
| `to_be_processed/` | one relocation `README.md` |
| `experiments/derive_constants/` | stub README pointing at `01_research/B_closures/B001_derive_constants/` |
| `experiments/trefoil/closure/` | stub README |
| `falsifier_registry/` | `README.md`, already copied to `10_docs/registry/` |

These describe a filesystem that no longer exists. Delete.

### 2. Build and cache residue — zero risk, high disk

`.venv/`, `build/`, `dist/`, `__pycache__/`, `.pytest_cache/`, `*.egg-info/` inside research packs.
All already gitignored, so this is a filesystem cleanup with no index effect.

The known large one: `SST_contact_billiard_hydrodynamic_falsifier_v0.2.0/.venv/` at ~280 MB.
`SST_Intrinsic_Modal_Swirl_Clock` had a `.venv` in seven of its version directories;
`SST_Threaded_Hole_Substrate` in all five. A per-family virtualenv is not a research artifact.

Delete after confirming each family's `run_01_install.cmd` can recreate it. That is the actual
precondition: a `.venv` is disposable only if it is reproducible.

### 3. Junction layer removal — the point of no return

This is where old paths stop working. Everything before it was reversible; this is not.

Preconditions, all of them:

- SP10 gate report has no unjustified `fail` rows.
- Every file previously in the break-set either resolves through `sst_workbench_paths` or has been
  confirmed dead. ~2,064 files were identified in the survey; the count remaining must be zero or
  explicitly accepted.
- `junctions.py verify` passes, so the registry matches reality before it is dismantled.

Remove level 2 (272 junctions, 73 scaffold directories) before level 1. Then strip `.git/info/exclude`.

**Recommended: do not do this in one pass.** Remove the junctions for one domain, run the full
suite, wait. The junctions cost nothing to keep. There is no deadline that justifies removing all
345 in an afternoon.

### 4. Archive deduplication — high risk, highest disk return

`09_archive/restore/` holds 607 zips in 29 themed buckets, roughly 2.4 GB. Some have an extracted
sibling in the tree, some do not. `INVENTORY_ARCHIVES.md` already distinguishes them, and
`scripts/consolidate_archives.py` already handles SHA-256 collisions.

Rules:

- **Never delete a zip whose contents are not extracted somewhere in the tree.** Thirteen Python
  scripts exist *only* inside archives; that count came from the existing inventory and must be
  re-verified against the post-migration tree, not trusted.
- Deduplicate only where a zip and its extracted sibling hash-match file for file.
- Deletion candidates go to a staging list, are reviewed, and are moved to
  `C:\workspace\projects\DELETE` — the existing `workbench_hygiene.py` convention — never unlinked
  directly.

The earlier analysis was explicit that archives should not be redistributed or re-extracted. That
holds. This step removes redundancy, not archives.

### 5. Old generated outputs

`*-outputs*/` directories now gitignored by SP03. Scientifically relevant runs were registered in
SP10's gate report and archived; the rest are reproducible by definition.

Same staging discipline as §4. The specific trap: an output directory that is *not* reproducible
because its input dataset has since changed. Check the run manifest's recorded dataset hash against
the current dataset before treating any output as disposable.

### 6. `.tmp.driveupload/` — outside the migration

~5.65 GB across 11 files, largest ~3.2 GB. Hidden Google Drive upload staging, explicitly not
research content.

This is **not** a research migration decision and this sub-plan does not delete it. Confirm with
Google Drive that no upload is pending, then remove it as a separate, independently decided
operation. It is listed here only so it is not forgotten.

## What is explicitly not deleted

Restating the non-goals, because this is the phase where they are most tempting to violate:

- **Old versions are not deleted** because git keeps them. Git keeping a file is not the same as a
  reproducible research pack being available. The 275 version directories stay.
- **Archives are not re-extracted.**
- **Blind and revealed artifacts are not merged.**
- **Outputs are not consolidated into one global directory.**
- **Old identifiers are not rewritten.** They live on in `legacy_paths`, `legacy_dir` and
  `path_map.csv` permanently.

## Tests to write

- `test_no_stubs.py` — none of the stub paths exist; nothing in the tree references them.
- `test_junction_removal_safe.py` — after removing a junction, the target directory still contains
  its full file count. Guards against `Remove-Item -Recurse` following a junction into its target,
  which is the way this phase could destroy real data.
- `test_archive_dedup_safety.py` — no zip is proposed for deletion unless every file inside it has a
  hash-matching extracted counterpart.
- `test_break_set_empty.py` — zero files still reference a pre-migration path, or the remaining set
  matches an explicit accepted list.

## Rollback

Sections 1 and 2 are recoverable from git or by re-running installers. Section 3 is recoverable by
re-running `bootstrap_junctions.cmd`, as long as `junction_registry.csv` is intact — do not delete
that file.

Sections 4 and 5 are **not** recoverable. That is why deletion candidates are staged to
`C:\workspace\projects\DELETE` rather than unlinked, and why this sub-plan is last.

## Done criteria

- Stubs gone, caches gone, `INVENTORY.md` regenerated and accurate.
- Junction layer removed domain by domain, with the full suite passing after each.
- Archive deduplication complete, with a written record of what was removed and the hash evidence
  for each.
- `10_docs/migration/` retains `path_map.csv`, `checksums.sha256`, `junction_registry.csv` and the
  gate report **permanently**. These are the provenance of the whole migration and are never
  cleaned up.
- Final tree statistics recorded against the SP00 baseline: 73 roots to 10 domains, 109 catalog
  families, disk before and after.
