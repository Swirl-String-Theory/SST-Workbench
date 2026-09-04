# SP00 FREEZE — SST-Workbench restructure baseline

Status: **FROZEN** · Recorded: 2026-09-04T13:38:15+02:00

## Content freeze commit

| Field | Value |
|-------|-------|
| SHA | `816505699e62f84cce2d4cc67ecb52c6e39c9d3c` |
| Short | `81650569` |
| Message | Add PyYAML to workbench requirements and fix workbench_tree ASCII help text. |
| Branch | `main` (ahead of `origin/main` by 3 at freeze time) |

Phase A commits under this freeze:

1. `925664e3` — Wien-Planck falsifier v0.4.0 pack (161 files)
2. `42ff7bf2` — private reveal keys (PFD v0.1.0 + Wien-Planck v0.2.2)
3. `81650569` — PyYAML requirement + `workbench_tree.py` ASCII help

## Baseline inventory numbers

| Metric | Epic baseline (2026-09-03) | Freeze measurement |
|--------|--------------------------:|-------------------:|
| Top-level families / roots | 73 | 73 (`pre-restructure-tree.json`) |
| Version directories | 275 | 266 (tree scan at `--max-depth 4`) |
| Tracked files (`git ls-files`) | 50,813 | 51,122 |
| Manifest rows (all on-disk files excl. `.git` / `.tmp.driveupload`) | — | 98,471 |
| Manifest tracked=`yes` | — | 51,110 |
| Checksums written | — | 51,214 (tracked + ignored >1 MB) |
| Longest tracked relative path | 231 chars | 231 chars |

Longest path (unchanged):

```text
SST_v0_8_19_routes_research/SST_v0_8_19_Planck_Routes_v3_preregistered_all_inclusive_pack/archive/legacy_extracted_v2_co...
```

Version-count drift (275 → 266) is expected: Phase A added Wien-Planck v0.4.0 while the
depth-4 tree scanner and epic inventory use slightly different version-name heuristics.
Use **73 roots** and **231 max path length** as the hard invariants; treat version count as
advisory until SP08 re-inventories from `FAMILY.yaml`.

## Provenance artifacts

All under `10_docs/migration/`:

| Artifact | Role |
|----------|------|
| `pre-restructure-tree.json` | Tree at max-depth 4 |
| `file_manifest.csv` | `path,size,mtime,tracked,ignored` |
| `checksums.sha256` | SHA-256 for tracked + large ignored |
| `path_map.csv` | 129 planned moves (125 `pending`, 4 `skipped`) |
| `baseline_tests.md` | As-found and post-fix test results |
| `open_questions.md` | Q1 / Q2 / Q3 answers with evidence |

## Reveal-key seal mismatch (open provenance item)

`SST_Phase_Feedback_Delay_Knot_Stability_Blind_Falsifier_v0.1.0`:

| Item | Value |
|------|-------|
| Committed seal (`blind_work/reveal_key_sha256.txt`) | `f42c0c15291167964f4e52d61fe884c63b87deb9bf01d54b3e048e2fd29f10f9` |
| SHA-256 of committed `private_reveal/reveal_key.json` | `6af05b09f9c26c74c2999c861660503bb0719e8bf1ec13547e4d71f1f2115ebb` |

The key was committed deliberately (Phase A commit 2) so the mismatch is visible rather than
silent. Wien-Planck v0.2.2 keys match the established v0.3.0 precedent and are unaffected.

## Quiescence

During planning, three root zips appeared then vanished within minutes:

- `Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.4.1.zip`
- `KnotLinkAtlas_v032_local_run_2026-09-04.zip`
- `SST_Parametric_Knot_Link_Seed_Atlas_v0.1.1.zip`

They were not deleted: they were relocated/extracted under
`Wien_Planck_SST_Field_Matter_Closure/`. OneDrive (`OneDrive`, `OneDrive.Sync.Service`) was
running; `.tmp.driveupload/` was absent at freeze time.

**Working tree accepted dirty** for concurrent unpacks outside Phase A (v0.4.1 pack tree,
atlas extracts, Galileo `*_BLIND_SOURCE` activity). Manifest and checksums cover the tree as of
the hash run; later SP00 consumers must not assume the untracked extractions are frozen content.

Root-file snapshot over an 8-second window at quiescence check: **unchanged**.

## Open questions (summary)

Full write-up: [open_questions.md](open_questions.md).

| ID | Verdict |
|----|---------|
| Q1 `git mv` ignored residue | **Yes — travels with the directory rename** |
| Q2 `sys.path` sibling imports | **No research-pack sibling *directory* imports;** two files import root `sst_gilbert_usability` (SP04 conversion target) |
| Q3 `gui` / `GUI` | **No collision** — 459 files under `gui/`, zero under `GUI/`, FS name `gui`. SP03 casing fix is a no-op |

Also recorded: `core.longpaths=true`; hyphenated `*-outputs/` gitignore gap confirmed (SP03).

## Baseline tests (post-fix)

| Suite | Result |
|-------|--------|
| `pytest scripts/` | **80 passed** |
| `unittest test_sst_gilbert_usability` | **4 passed** |
| `pytest verification-suites/embedded-knots/` | **1 skipped** |

As-found was 58 passed / 9 failed (missing PyYAML). See [baseline_tests.md](baseline_tests.md).

## Next

SP00 done criteria met. Proceed to SP01 (path resolver) only after this freeze commit is on the
branch you will migrate from. Nothing in SP00 moves research packs.
