---
name: SP01 path resolver
overview: ""
todos:
  - id: t00
    content: Create `07_scripts/sst_workbench_paths/` module
    status: completed
  - id: t01
    content: Implement `WORKBENCH_ROOT` / `DATA_ROOT` / `KNOT_DATASET` / … resolution
    status: completed
  - id: t02
    content: Implement `resolve_family(catalog_id[, version])` against `path_map.csv`
    status: completed
  - id: t03
    content: Create matching `07_scripts/paths.cmd`
    status: completed
  - id: t04
    content: Write `10_docs/architecture/path_resolution.md`
    status: completed
  - id: t05
    content: List seven absolute `paths.cmd` conversion targets (do not convert yet)
    status: completed
  - id: t06
    content: Add `test_workbench_paths.py`
    status: completed
  - id: t07
    content: Add `test_resolve_family.py`
    status: completed
  - id: t08
    content: Add `test_paths_cmd.py`
    status: completed
  - id: t09
    content: "Done-criteria: identical resolution from ≥3 depths; all three tests green"
    status: completed
isProject: false
---

# SP01 — Central path resolver

Status: `DONE` · Priority: P0 · Risk: low · Depends on: SP00

## Todos

Progress tracker — checkboxes include completed work so status is obvious at a glance.

- [x] Create `07_scripts/sst_workbench_paths/` module
- [x] Implement `WORKBENCH_ROOT` / `DATA_ROOT` / `KNOT_DATASET` / … resolution
- [x] Implement `resolve_family(catalog_id[, version])` against `path_map.csv`
- [x] Create matching `07_scripts/paths.cmd`
- [x] Write `10_docs/architecture/path_resolution.md`
- [x] List seven absolute `paths.cmd` conversion targets (do not convert yet)
- [x] Add `test_workbench_paths.py`
- [x] Add `test_resolve_family.py`
- [x] Add `test_paths_cmd.py`
- [x] Done-criteria: identical resolution from ≥3 depths; all three tests green

**Next:** Resolver shipped: sst_workbench_paths + paths.cmd + resolve_family.

~2,064 files hardcode a path that a move breaks. This sub-plan gives them somewhere better to point,
before anything moves. It changes no directory layout.

## Why generalize rather than invent

Eight path conventions already coexist in the repo. A ninth would make things worse. Two of the
existing ones are good and get promoted:

- `Knot_Library/SST_Knot_Library/SST_Knot_Library_v0.2.0/sst_knotlib/library_root.py` —
  environment override, then upward marker search, then sibling probe. This is the right shape.
- `SST_Fourier_vs_Ideal_Blind_Falsifier/.../config/paths.cmd` — a `paths.cmd` include with
  `if not defined X set "X=..."`, so any variable can be overridden before calling a `run_*.cmd`.
  This is the right shape for the CMD side.

The name `SST_WORKBENCH_ROOT` is already in use in seven `config/paths.cmd` files, hardcoded
absolute. Keep the name, fix the resolution.

## Deliverables

### 1. `07_scripts/sst_workbench_paths/` — the Python module

```python
WORKBENCH_ROOT      # SST_WORKBENCH_ROOT, else upward search for the root marker
DATA_ROOT           # SST_DATA_ROOT,      else WORKBENCH_ROOT / "03_data"
KNOT_DATASET        # SST_KNOT_DATASET,   else DATA_ROOT / "A_knots/04_knotplot/final"
IDEAL_SOURCES       # SST_IDEAL_SOURCES
KATLAS_SOURCES      # SST_KATLAS_SOURCES
FSERIES_ROOT        # SST_FSERIES_ROOT
```

Resolution order for each: explicit argument, environment variable, upward search from
`Path(__file__)` for the root marker, packaged default. Never a bare `parents[N]`.

The root marker is a `.sst-workbench-root` file written at the repo root in SP03. Marker search is
what makes the module immune to depth changes — a pack that moves from 2 levels deep to 4 keeps
working with no edit.

### 2. `resolve_family(catalog_id)` — the important part

```python
resolve_family("A042")  # -> .../01_research/A_falsifiers/A042_quantum_galileo_action_gauge_closure
resolve_family("A039", version="v0.1.1")
```

Backed by the catalog index built in SP08. This is what makes cross-pack references survive not
just this restructure but every future one: a pack that needs another pack asks for `A021`, never
for a path.

Until SP08 exists, `resolve_family` reads `path_map.csv` and resolves through it. That is
deliberate — it means the resolver works during the migration, not only after.

### 3. `07_scripts/paths.cmd` — the CMD include

Mirrors the same variables and the same override semantics, so `.cmd` run scripts get the identical
resolution without a Python round-trip:

```bat
if not defined SST_WORKBENCH_ROOT call :find_root
if not defined SST_DATA_ROOT set "SST_DATA_ROOT=%SST_WORKBENCH_ROOT%\03_data"
if not defined SST_KNOT_DATASET set "SST_KNOT_DATASET=%SST_DATA_ROOT%\A_knots\04_knotplot\final"
```

`:find_root` walks up from `%~dp0` looking for `.sst-workbench-root`.

### 4. Migration guidance, not migration

This sub-plan does **not** rewrite the 2,064 files. It publishes the resolver and documents the
replacement patterns in `10_docs/architecture/path_resolution.md`:

```text
..\..\KnotPlot\knots\final        ->  %SST_KNOT_DATASET%
Path(__file__).parents[2]         ->  sst_workbench_paths.WORKBENCH_ROOT
'../../Ideal_Sources'             ->  sst_workbench_paths.IDEAL_SOURCES
C:\workspace\...\KnotPlot\knots   ->  %SST_KNOT_DATASET%
```

Packs are converted opportunistically: when a pack is touched for any other reason, its paths get
converted. Bulk conversion is explicitly out of scope — junctions make it unnecessary, and a
2,000-file codemod before any move is verified would be reckless.

## Tests to write

- `test_workbench_paths.py` — resolution order for each variable; env override wins; marker search
  finds the root from an arbitrary depth; missing marker raises a clear error rather than silently
  returning the filesystem root.
- `test_resolve_family.py` — known catalog ID resolves; unknown ID raises; `version=` selects the
  right subdirectory; resolution works through `path_map.csv` before SP08 and through the catalog
  index after.
- `test_paths_cmd.py` — invokes `paths.cmd` in a subprocess from several depths and asserts the
  variables match what the Python module returns. The two implementations must not drift.

## Rollback

Delete the module and the include. Nothing depends on it yet.

## Done criteria

- Both implementations resolve identically from at least three different directory depths.
- `resolve_family()` works against `path_map.csv`.
- All three test files pass.
- The seven `config/paths.cmd` files with absolute `SST_WORKBENCH_ROOT` are listed in
  `10_docs/architecture/path_resolution.md` as the first conversion targets — listed, not yet
  converted.
