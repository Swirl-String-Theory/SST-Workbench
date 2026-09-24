# Pre-refactor content audit — 2026-09-13

Google Drive did not wipe the research tree. Tracked file count rose from 50,957 (`main-sept-4`) / 51,122 (SP00 freeze) to 69,815 on `HEAD`. The 21 git blobs that are absent from `HEAD` all still have a successor on disk or in git under a renamed path.

True content loss here means: an old path has no `HEAD` destination after `path_map.csv` remapping, **and** that exact blob is not in `HEAD`.

## Verdict

| Question | Answer |
|----------|--------|
| Missing research families vs pre-refactor | No. 73 roots were catalogued; content is under `01_research` … `10_docs`. |
| Missing tracked blobs with no successor | **0 after classification below.** The raw scanner listed 21, all explained. |
| Drive Desktop conflict copies in packs | Cleared: hash-identical copies deleted; unique `(1)` files quarantined. |
| `gdrive:SST-Workbench` rclone remote | Present; top-level matches the catalog domains. Not used as restore source. |

## Git blob comparison

### main-sept-4 (`e06410b84`)

- old files: `50957`
- HEAD files: `69815`
- present after remap: `45681`
- same blob at another HEAD path: `5255`
- raw scanner “unexpected lost blobs”: `21`

### SP00 freeze (`81650569`)

Same 21 paths (freeze is three commits after sept-4: Wien-Planck v0.4.0, reveal keys, PyYAML).

### What those 21 actually are

1. **14 restructure plans** — renamed `.md` → `.plan.md` and then edited, so the old blob is gone. Files remain, e.g. [`.cursor/plans/restructure/RESTRUCTURE_EPIC.plan.md`](.cursor/plans/restructure/RESTRUCTURE_EPIC.plan.md).
2. **2 KnotPlot output zips** — still on disk at `09_archive/restore/KnotPlot/` (`*.zip` is gitignored, so they are not in the `HEAD` tree).
3. **2 A035 `run_all.cmd` files** — SP09 renamed `SST_SCII_…_v0.1.1` / `SST_SCIII_…_v0.1.0` to `A035-v0.1.1` / `A035-v0.1.0`. `FAMILY.yaml` still lists those version directories.
4. **2 Trefoil Closure `.exp`/`.lib`** — rebuildable MSVC link artifacts; unique scripts live under `09_archive/trefoil_closure/root_remnants/` ([delete_retirement.md](delete_retirement.md)).
5. **`test_sst_gilbert_usability.py`** — moved to [`07_scripts/test_sst_gilbert_usability.py`](../../07_scripts/test_sst_gilbert_usability.py).

Raw rows: [pre_refactor_lost_blobs.csv](pre_refactor_lost_blobs.csv).

## Ignored freeze-manifest files on disk

The freeze `file_manifest.csv` listed 47,361 ignored paths (IDE files, unpacked outputs, local zips).

- present at old or remapped path: `532`
- expected missing (`outputs/`, `build/`, caches): `18635`
- other missing vs freeze paths: `28194`

That last bucket is **not** “Drive deleted the packs”. The sample is mostly:

- `.idea/*.iml` (gitignored IDE state)
- `Restore_Archives/…` zips that now live under `09_archive/restore/KnotPlot/` (and siblings), not at the exact remapped prefix
- other gitignored local residue from the freeze working tree

## Google Drive conflict copies

Untracked Drive Desktop names (`foo (1).ext` / `foo (1)/`) only. Tracked names such as `Infographic(1).png` were left alone.

| Action | Count (final tree) |
|--------|-------------------:|
| Hash-identical duplicate deleted | 35 template files + remaining pack duplicates from the first pass |
| Unique `(1)` files quarantined | 28 files under [`09_archive/drive_conflicts/`](../../09_archive/drive_conflicts/) |
| Packs still containing Drive `(1)` copies | 0 |

Unique copies differed in hash from their sibling (typical CRLF / later edit). They are still readable in quarantine, including `.gitignore (1)` and several `run_all (1).cmd` files.

Ledger (includes a failed first apply plus a nested re-run that was flattened): [drive_conflict_cleanup_20260913.jsonl](drive_conflict_cleanup_20260913.jsonl).

Helpers: [`07_scripts/cleanup_drive_conflict_copies.py`](../../07_scripts/cleanup_drive_conflict_copies.py), [`07_scripts/audit_pre_refactor_content_loss.py`](../../07_scripts/audit_pre_refactor_content_loss.py).

## rclone

`gdrive:` exists. `rclone lsf gdrive:SST-Workbench --max-depth 1` shows the catalog domains (`01_research/` … `10_docs/`). Local remains source of truth; this listing was not a download.
