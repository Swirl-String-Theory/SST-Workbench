# A058-v0.3.5 launcher repair

## Root cause

In v0.3.3 `resolve_launcher` did `if not wd.is_absolute(): raise RuntimeError('Shortcut WorkingDirectory is relative; refusing to infer a root')`. The v0.3.3 hotfix therefore fixed the use of `.lnk` but rejected valid shortcuts whose Start-in was relative. This failure happens prior to calling KnotPlot. Existing source and results are not implicated.

## Changes

- `tools/shortcut_runtime.py`: relative working-directory candidates and immutable, explicit provenance tags; optional absolute `workdir_override`.
- `tools/distribution_audit.py`: `--workdir` override for `RUN_SAFE_PROBES`.
- `tools/shortcut_check.py`: read-only `CHECK_SHORTCUT` launcher inspection.
- `run_all.cmd`: new diagnostic command.
- `tests/test_shortcut_runtime.py`: relative dot, EXE-only, link-only, ambiguous/missing, explicit override, and inspector regression tests.

This is an **execution/launcher fix only**. No source-engine change, no altered historical A058 gate ledger, no reveal, and no new blind campaign. Absolute export routing under the probe directory stays the same as v0.3.3.

## Fail-closed conditions

Nonexistent shortcut target; nonexistent configured folder; relative folder not found below either candidate base; two different candidate folders; non-absolute `--workdir`; existing native outputs; unavailable Windows COM. The user may resolve ambiguity explicitly with `--workdir`.


## v0.3.5: Windows shortcut %ENVVAR% correction

A `.lnk` may contain `Start in: %SST-Workbench%\01_research\...\A058-v0.3.2`.
The previous v0.3.4 runner incorrectly attempted to treat that string as a
plain relative path. v0.3.5 first expands Windows `%VAR%` placeholders. If a
variable is unavailable to Python, it may be resolved from a uniquely named
ancestor directory of the shortcut itself. Unmatched placeholders fail closed.

**The shortcut target and shortcut file are never modified.**
The KnotPlot process inherits the resolved `Start in` directory, and the
KnotPlot script references per-probe inputs/outputs by explicit absolute paths
under `A058_probes/`. This is independent of the executable install folder.

Preflight and run without changing the existing .lnk:

```bat
run_all.cmd CHECK_SHORTCUT --exe ".\KnotPlot.lnk"
run_all.cmd RUN_SAFE_PROBES --exe ".\KnotPlot.lnk" --out ".\A058_probes" --timeout 120
```

If older attempted launches have created native output/log files, use a NEW
output directory to prevent overwriting committed evidence. This fix remains
locally tested only; final qualification requires the native Windows run.


## v0.3.6: original defect shown by user logs

2026-10-22: `.lnk` resolution PASS; `run_safe_probes` Python preflight raised FileNotFoundError on `A058_probes/dstep_1/A058_seed.kpf`. Previous attempts showed existing runtime evidence and empty/new directories. The actual 2026 KnotPlot binary was not yet started for the failing seed-input attempt. `probe_preflight` validates both seeds/scripts/hashes; read-only `CHECK_PROBES` exposes inputs; optional `--dist` generates only a nonexistent directory. No attempt to fix/re-key/delete earlier runs.
