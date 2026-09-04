# SP00 open questions

Evidence recorded during freeze. Answers are binding for later sub-plans.

## Q1 — Does `git mv` on a directory carry ignored residue?

**Answer: yes.**

Throwaway repo test (`%TEMP%\sp00_gitmv_q1`):

1. Created `olddir/` with tracked `src/main.py` and ignored `.venv/Lib/x.py` + `build/out.o`.
2. Ran `git mv olddir newdir`.
3. Result: `newdir/.venv/Lib/x.py` and `newdir/build/out.o` both present; `olddir` gone;
   git status shows only the tracked rename `olddir/src/main.py -> newdir/src/main.py`.

**Implication for SP04–SP07:** a plain `git mv` is sufficient to carry pack-local
`.venv`, `build/`, and ignored outputs. No mandatory `robocopy /MOVE` second stage.

## Q2 — Which packs import siblings through `sys.path`?

**Answer: no research-pack imports a sibling top-level *directory* by name.**
Numeric-prefixed catalog domains therefore do not break those imports.

Scan: 301 `*.py` files call `sys.path.insert/append/extend`. Of those, only two import a
name that also exists as a workbench top-level path, and both are tooling:

| File | Inserts | Imports from root |
|------|---------|-------------------|
| `SST_minimal_falsification_harness/.../sst_minimal_falsification.py` | `parents[2]` | *(no sibling dir import in module header)* |
| `SST_ideal_trefoil_biot_research/sst_trefoil_bs/ideal_source.py` | `parents[2]` | `sst_gilbert_usability` (root `.py` module) |
| `KnotPlot/ridgerunner/gilbert_ab_to_xyz.py` | `BUNDLE.parents[1]` | `sst_gilbert_usability` (root `.py` module) |
| `scripts/falsifier_registry.py` consumers | scripts dir | `falsifier_registry` (the `scripts/` module) |

Most `sys.path` inserts exist to reach the installed `sstcore` package or local pack code.
The two `sst_gilbert_usability` importers **will break when SP04 moves that module into
`07_scripts/`** unless converted to the SP01 resolver (or `07_scripts` is put on
`PYTHONPATH`). Recorded as an SP01/SP04 conversion target, not as a numeric-prefix problem.

## Q3 — Is the `gui` / `GUI` case divergence one directory or two?

**Answer: no collision. One directory, lowercase `gui/` everywhere.**

| Evidence | Value |
|----------|------:|
| `git ls-files` under `gui/` | 459 |
| `git ls-files` under `GUI/` | 0 |
| Filesystem directory name | `gui` |

SP03 §4 (temporary rename to fix index casing) is a **no-op**. The restructure plan's
`GUI/` references should use `gui/` on disk (seed_path_map already normalizes this).

## Related preconditions already satisfied

- `git config core.longpaths` = `true` (local).
- Hyphenated output gitignore gap confirmed live: `**/*_outputs/` did not match
  `...Falsifier_v0.4.0-outputs/` (those files were committed in Phase A by design;
  SP03 still adds the hyphenated patterns for future runs).
