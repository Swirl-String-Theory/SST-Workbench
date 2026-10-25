# A006 ForceGrid analyzer repair v0.5.0c3

**Scope:** fixes a false script integrity error in `run_all.cmd FORCEGRID ANALYZE` on Windows. `PLAN.json` stores SHA-256 of canonical LF-encoded text, while Windows-generated scripts use CRLF. The existing `force_grid_v050c.py` mistakenly checks raw bytes in `analyze()`; the recovery installers used normalized line endings, hence their PASS did not fix ANALYZE.

## Install in the existing A006-v0.5.0 project directory

1. Unzip this package under `patch_staging/A006_FORCEGRID_ANALYZER_FIX_v0.5.0c3/`.
2. Run:

```bat
py -3 patch_staging\A006_FORCEGRID_ANALYZER_FIX_v0.5.0c3\repair.py --base . --check
py -3 patch_staging\A006_FORCEGRID_ANALYZER_FIX_v0.5.0c3\repair.py --base . --apply
run_all.cmd FORCEGRID TEST
run_all.cmd FORCEGRID ANALYZE
```

A backup of **only the analyzer module** is stored under `patch_backups/A006_v0.5.0c3_analyzer_fix`. No changes to KPS scripts, KnotPlot RC, run_all, PLAN, native CSV, or XYZ datasets. `--rollback` is available with automatic hash verification.

`--check` checks the full 14-arm plan using canonical script SHA-256, and refuses any actual content change. Idempotent on already-patched modules. This patch does not execute or certify KnotPlot dynamics.

**Additional observations from the uploaded 14-arm data:** all 70 XYZ checkpoints exist; identical initial states; the two CLOSE branches are byte-identical to BEND_OFF at checkpoints 1/8/32/128, and AMECH_MATCH_P2 is identical to AMECH_MATCH_ELEC. This deserves command-effective-status investigation, not silent PASS of force sensitivity.
