# SP00 — Freeze and provenance

Status: `PLANNED` · Priority: P0 · Risk: low · Depends on: nothing

Nothing moves in this sub-plan. Its only job is to make every later move reversible and to resolve
three questions that would otherwise be discovered mid-migration.

## Preconditions

- Working tree committed or explicitly accepted as dirty (record which).
- No long-running campaign writing into the tree.

## Steps

### 1. Baseline test run

Record the result, including failures, in `10_docs/migration/baseline_tests.md`:

```powershell
python -m pytest scripts/ -q
python -m unittest test_sst_gilbert_usability
python -m pytest verification-suites/embedded-knots/ -q
```

A failure here is a pre-existing condition, not a migration regression. Later phases compare
against this baseline, not against green.

### 2. Provenance artifacts

Generate into `10_docs/migration/`:

- `pre-restructure-tree.json` — full tree at `--max-depth 4` via `scripts/workbench_tree.py`. The
  existing default of 3 is not enough to capture version-directory internals.
- `file_manifest.csv` — `path,size,mtime,tracked,ignored` for every file outside `.git` and
  `.tmp.driveupload`.
- `checksums.sha256` — SHA-256 for every tracked file, plus every ignored file above 1 MB. Full
  hashing of ~12 GB is feasible once; do it now, not later.
- `path_map.csv` — the machine-readable mapping, seeded from
  [RESTRUCTURE_PLAN_v0.1.md](RESTRUCTURE_PLAN_v0.1.md).

### 3. `path_map.csv` schema

```text
old_path,new_path,domain,letter,catalog_id,kind,phase,junction,status,note
```

- `kind` — `code` | `data` | `output` | `tooling` | `archive` | `vendored` | `stub`
- `phase` — `SP04` … `SP11`
- `junction` — `yes` | `no`; whether a compat junction is created at `old_path`
- `status` — `pending` | `moved` | `verified` | `reverted` | `skipped`

Every move writes its row before executing and updates `status` after. A move without a row is a
bug.

### 4. Resolve the three open questions

**Q1 — Does `git mv` on a directory carry ignored residue?** `git mv olddir newdir` performs a
filesystem rename, so ignored content inside (`.venv`, `build/`, `outputs/`) should travel with it.
Verify on a throwaway copy rather than assuming. If it does not, every move needs a `robocopy /MOVE`
second stage and SP04–SP07 change shape.

**Q2 — Which packs import siblings through `sys.path`?** Numeric-prefixed directories can never be
Python packages: `import 01_research...` is a syntax error. Enumerate every file that inserts the
workbench root into `sys.path` and then imports by top-level name. Known starting points:

- `SST_minimal_falsification_harness/.../sst_minimal_falsification.py:56` — `parents[2]`
- `SST_ideal_trefoil_biot_research/sst_trefoil_bs/ideal_source.py:45` — `parents[2]`
- `KnotPlot/ridgerunner/gilbert_ab_to_xyz.py:27` — `BUNDLE.parents[1]`

Most of these insert the root to reach `sstcore`, which is installed, not a sibling directory — in
that case the numeric prefix is harmless. Confirm one by one. Anything that genuinely imports a
sibling top-level directory must be converted to `resolve_family()` in SP01.

**Q3 — Is the `gui` / `GUI` case divergence one directory or two?** Git tracks 459 files under
`gui/`; the filesystem shows `GUI/`. Determine whether the index simply has stale casing or whether
two directories once existed. This decides whether SP03's fix is a rename or a merge.

### 5. Freeze marker

Write `10_docs/migration/FREEZE.md` recording the commit SHA, timestamp, and the baseline numbers:
73 roots, 275 version directories, 50,813 tracked files, longest tracked path 231 characters.

## Tests to write

In `07_scripts/` (still `scripts/` at this point):

- `test_path_map.py` — `path_map.csv` parses; every `old_path` exists on disk; no `new_path`
  appears twice; every `catalog_id` matches `CATALOG_v0.1.md`; every row has a valid `phase` and
  `status`.
- `test_manifest_integrity.py` — `checksums.sha256` covers every tracked file in `file_manifest.csv`.

## Rollback

Nothing to roll back — no files move. Delete `10_docs/migration/` to start over.

## Done criteria

- All four provenance artifacts exist and `test_path_map.py` passes.
- Q1, Q2 and Q3 answered in writing, each with the evidence that settled it.
- Baseline test results recorded, failures included.
- `path_map.csv` has one row per planned move, all `status=pending`.
