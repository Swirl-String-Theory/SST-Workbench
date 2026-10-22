# A006 v0.5.0c1 — ForceGrid dispatcher recovery

**Purpose:** Recover `run_all.cmd FORCEGRID ...` when the v0.5.0c installer reports `already installed or partial state`, but the command still falls through to `selection_v050.py`.

This recovery handles both an uninstalled v0.5.0c and common *partial installations*. It does not change seeds, RoundFolded geometry, `Output/v050` or pre-existing ForceGrid measurements. This is NOT an additional dynamics campaign or a new geometrical seed release.

## Windows installation

Unpack this ZIP inside the project as `patch_staging\A006_FORCEGRID_RUNNER_REPAIR_v0.5.0c1\`. From the A006 project root:

```bat
py -3 patch_staging\A006_FORCEGRID_RUNNER_REPAIR_v0.5.0c1\repair.py --base . --check
py -3 patch_staging\A006_FORCEGRID_RUNNER_REPAIR_v0.5.0c1\repair.py --base . --apply
run_all.cmd FORCEGRID TEST
run_all.cmd FORCEGRID PLAN
run_all.cmd FORCEGRID BUILD
```

`--check` **reports each separate component** (`grid_module`, `grid_dispatch`, `grid_aliases`, `grid_plan`), rather than aborting just because one component is already present. `--apply` only fills in what is missing. An existing plan is validated against the fixed seed hash and checksummed scripts; it is never regenerated. Existing output without a plan leads to a refusal instead of overwriting possibly valuable results. Existing aliases or modules that differ are never silently overwritten.

The installer backs up `run_all.cmd` and `knotplotrc.kps` under `patch_backups/v050c1_RUNNER_RECOVERY/`. Re-run of `--apply` on a complete installation is a **no-op**. The repair attempts to restore original runner/RC if installation fails; generated staging output, if any, is retained.

## `FORCEQUAL` versus `FORCEGRID`

`FORCEQUAL` was supplied by the **separate** v0.5.0b patch. Your v0.5.0c package supports direct installation on v0.5.0a, without v0.5.0b. Thus `FORCEQUAL` may genuinely be unavailable.

- `FORCEGRID TEST`, `PLAN`, `BUILD` and `ANALYZE`: supported by the v0.5.0c module (14 arms).
- If the v0.5.0b module already exists and only its dispatcher is missing, this repair restores `FORCEQUAL` too.
- If the v0.5.0b module is absent, **do not run `FORCEQUAL`**. ForceGrid contains the six original BEND/force isolation conditions plus eight newer conditions.

For immediate diagnostics, bypass the dispatcher:

```bat
py -3 tools\force_grid_v050c.py TEST
py -3 tools\force_grid_v050c.py PLAN
```

## KnotPlot GUI

Restart KnotPlot after the alias update. The short aliases remain `fgB0`, `fgB1`, `fgB10`, `fgB100`, `fgM`, `fgE`, `fgA14`, `fgAM`, `fgAM0`, `fgAM2`, `fgD5`, `fgD10`, `fgC10`, `fgC30`.

Scripts contain **no `stop`**, use the supported native CSV format `/I,/N,/l,/g`, and require a real GUI execution to create result data. `FORCEGRID BUILD` only prepares the scripts. Collision mode and damping must be verified in actual KnotPlot runtime; prepared scripts do not certify either.

## Guarded rollback

```bat
py -3 patch_staging\A006_FORCEGRID_RUNNER_REPAIR_v0.5.0c1\repair.py --base . --rollback
```

Rollback refuses to overwrite subsequent manual edits. It restores only the runner and rc; it does not delete generated outputs or copied modules.

## Test coverage

Fixture tests cover: clean base, partial v0.5.0c with aliases/scripts/plan but restored runner, already-working v0.5.0c, present v0.5.0b module, idempotent reapply, guarded rollback, protected existing aliases, user-modified module, and orphan runtime outputs.

**Evidence:** static/integration tests on a separately extracted A006 v0.5.0a ZIP; KnotPlot GUI execution and Windows CMD process execution have *not* been performed here.
