# A058-v0.3.4 launcher repair

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
