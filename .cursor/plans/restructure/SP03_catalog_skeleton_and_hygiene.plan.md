---
name: SP03 catalog skeleton and hygiene
overview: ""
todos:
  - id: t00
    content: Create 10-domain + letter skeleton (`.gitkeep` / README per leaf)
    status: completed
  - id: t01
    content: "Write `.sst-workbench-root` marker (`catalog_schema: 1`)"
    status: completed
  - id: t02
    content: Ensure `core.longpaths` / Windows LongPathsEnabled
    status: completed
  - id: t03
    content: "Confirm/fix `gui` casing (SP00 Q3: already lowercase — verify no-op)"
    status: completed
  - id: t04
    content: Extend `.gitignore` for `*-outputs*` and `keys/`
    status: completed
  - id: t05
    content: Tests for skeleton / marker / gitignore
    status: completed
  - id: t06
    content: "Done-criteria: skeleton present; hygiene tests green"
    status: completed
isProject: false
---

# SP03 — Catalog skeleton and repo hygiene

Status: `DONE` · Priority: P1 · Risk: low · Depends on: SP00

## Todos

Progress tracker — checkboxes include completed work so status is obvious at a glance.

- [x] Create 10-domain + letter skeleton (`.gitkeep` / README per leaf)
- [x] Write `.sst-workbench-root` marker (`catalog_schema: 1`)
- [x] Ensure `core.longpaths` / Windows LongPathsEnabled
- [x] Confirm/fix `gui` casing (SP00 Q3: already lowercase — verify no-op)
- [x] Extend `.gitignore` for `*-outputs*` and `keys/`
- [x] Tests for skeleton / marker / gitignore
- [x] Done-criteria: skeleton present; hygiene tests green

**Next:** Skeleton seeded; placeholders are _NAMESPACE.md; longpaths global.

Creates the empty target structure and fixes three repo-level problems that would otherwise
corrupt the first move. **No research pack moves in this sub-plan.**

## 1. The skeleton

Create the ten domains with their letter subdirectories. Every leaf gets a `.gitkeep` and a
one-line `README.md` stating what belongs there — an empty namespace with no statement of purpose
is an invitation to put the wrong thing in it.

```text
01_research/{A_falsifiers,B_closures,C_dynamics,D_benchmarks,E_pipelines,F_exploratory}/
02_libraries/{A_knot_geometry,B_knot_data,C_finite_core,D_numerics}/
03_data/{A_knots,B_external,C_reference,D_generated}/
04_tools/{A_geometry,B_crawlers,C_fabrication,D_proof}/
05_apps/
06_templates/
07_scripts/
08_third_party/
09_archive/
10_docs/{inventory,architecture,migration,registry}/
```

`02_libraries/D_numerics/` is created empty on purpose. Nothing belongs there today; it exists so
that shared numerical kernels extracted later do not require another restructure.

## 2. Root marker

Write `.sst-workbench-root` at the repo root. This is the anchor SP01's upward search looks for.
Its content is the catalog schema version, so a future incompatible change is detectable:

```text
catalog_schema: 1
```

## 3. `core.longpaths`

The longest tracked relative path is 231 characters. With the root prefix
`C:\workspace\projects\SST-Workbench\` that is 267 — already past the Windows `MAX_PATH` of 260 —
and 543 tracked paths exceed 220 characters. `core.longpaths` is currently unset at every scope.

```powershell
git config core.longpaths true
```

Also verify the Windows-level `LongPathsEnabled` registry value, because `core.longpaths` covers
git's own operations but not every tool that later walks the tree.

The catalog makes paths *shorter* overall, but the transition is the dangerous moment: during
stage 1 a family sits at its new deeper location while still carrying its old long version
directory name. That is the peak, and it happens before SP09 shortens anything.

## 4. The `gui` / `GUI` case collision

Git tracks 459 files under `gui/`; the filesystem shows `GUI/`. On a case-insensitive filesystem
this stays invisible until a rename touches it, at which point git can produce a tree with both
casings and a checkout on Linux or macOS gets two directories.

SP00 Q3 determines whether this is stale index casing or two genuinely distinct histories. If it is
stale casing, fix it through a temporary name so git records a real rename:

```powershell
git mv GUI _gui_tmp
git mv _gui_tmp GUI
git commit -m "Normalize GUI directory casing in the index"
```

Do this **before** SP06 moves `GUI/` into `05_apps/`. Renaming and re-casing in one step is how you
get a corrupted tree.

## 5. `.gitignore`

The current file already covers `__pycache__/`, `.venv`, `.pytest_cache/`, `build/`, `dist/`,
`*.zip`, `**/*_outputs/`, `**/outputs/` and `**/outputs_*/`. What it misses is the **hyphenated**
output convention this repo actually uses:

```gitignore
*-outputs/
*-outputs_BLIND/
*-outputs_REVEALED/
```

`**/*_outputs/` with an underscore does not match `SST_..._Falsifier_v0.1.1-outputs/`. Add the
hyphenated forms, plus:

```gitignore
# Catalog compat layer (junction targets are tracked; junctions are not)
# Junction names live in .git/info/exclude, never here.

# Reveal keys are never committed unless a family is explicitly unblinded
01_research/*/*/keys/
```

Leave `*.zip` as it is. The existing force-add workflow through `scripts/git_add_small_zips.py` and
`scripts/output_zip_policy.py` depends on it, and changing zip policy mid-migration would confuse
the 50 MB staging rule.

## 6. Numeric prefixes are not Python packages

Document in `10_docs/architecture/path_resolution.md`: `import 01_research...` is a syntax error,
permanently. Any code that inserts the workbench root into `sys.path` and imports a sibling by
top-level directory name must use `resolve_family()` instead.

SP00 Q2 produced the list. If it is empty — likely, since most such inserts exist to reach the
installed `sstcore` package rather than a sibling directory — record that it is empty and why, so
the question is not reopened later.

## Tests to write

- `test_catalog_skeleton.py` — every domain and letter directory from `CATALOG_v0.1.md` exists;
  every leaf has a `README.md`; no leaf outside `02_libraries/D_numerics/` is empty once SP05 has
  run.
- `test_root_marker.py` — `.sst-workbench-root` exists, parses, and `sst_workbench_paths` finds it
  from at least four depths.
- `test_gitignore_outputs.py` — the hyphenated output patterns match real example names taken from
  the current tree, and do **not** match a source directory that merely contains the word outputs.

## Rollback

Delete the skeleton directories, `.sst-workbench-root`, and revert the `.gitignore` and
`core.longpaths` changes. The GUI casing fix is a real commit and is reverted with `git revert`.

## Done criteria

- Skeleton exists, every leaf documented.
- `core.longpaths` set; a path over 260 characters can be created and checked out.
- GUI casing resolved and committed as its own commit, separate from anything else.
- `.gitignore` matches the hyphenated output convention; the three tests pass.
- The numeric-prefix question is answered in writing, including if the answer is "no impact".
