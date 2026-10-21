# A058-v0.3.1 REPAIR — non-destructive diagnostic coordinator

This is a **complete coordinator-only release**, **not a replacement scientific engine**. It patches v0.3.0 `bridge.py` to preserve per-run native stdout (PRIVATE) and structured failure records. A058-v0.2.9/v0.2.10 frozen scientific source, private commitments, 271-condition experiment and old gate ledgers are unchanged. It fixes a confirmed structural launch bug: the cloned `.sst_framework_root` is relative to the original v0.2.9 directory, not its new clone directory. v0.3.1 resolves the pinned Framework v1.0.8 relative to the **original** source location and passes its absolute root via `SST_FALSIFIER_FRAMEWORK_ROOT`, without touching frozen source bytes. It also captures native diagnostic evidence; a Windows retest is required to establish whether further errors remain. No native Windows execution was possible in this release environment.

## Use against your existing v0.3.0 clone (recommended)

From new extracted `A058-v0.3.1-REPAIR` folder, where `--legacy` is the path to the existing v0.3.0 folder:

```cmd
run_all.cmd SELFTEST
run_all.cmd DIAGNOSE --legacy "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A058_KnotPlot_Parameter_Sensitivity_Relaxation_Robustness\A058-v0.3.0"
run_all.cmd AUDIT_CONTROLS --legacy "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A058_KnotPlot_Parameter_Sensitivity_Relaxation_Robustness\A058-v0.3.0"
run_all.cmd STATUS --legacy "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A058_KnotPlot_Parameter_Sensitivity_Relaxation_Robustness\A058-v0.3.0"
```

The `--legacy` flag enables **read-only provenance attachment** to that existing clone. The source `.sst_framework_root` is *never rewritten*, because its bytes are part of the frozen manifest. The absolute framework path is passed to the original science process only as an environment variable, and the launcher rejects any framework version other than v1.0.8. For a fresh clone ONLY: `run_all.cmd PREPARE --source "C:\full\path\A058-v0.2.9"`; a second PREPARE refuses overwrite.

## Re-run after examining diagnostics

Only if `DIAGNOSE` and the original engine's native logs identify and resolve the blocking **non-scientific** problem, rerun the minimum affected phase:

```cmd
run_all.cmd INSTALL --legacy "C:\...\A058-v0.3.0"
run_all.cmd FREEZE --legacy "C:\...\A058-v0.3.0"
run_all.cmd BASIC --legacy "C:\...\A058-v0.3.0"
run_all.cmd 2048 --legacy "C:\...\A058-v0.3.0"
run_all.cmd 32768 --legacy "C:\...\A058-v0.3.0"
run_all.cmd FULL --legacy "C:\...\A058-v0.3.0"
```

**Do not blindly run all stages.** `INSTALL` may rewrite calibration; `FREEZE` must preserve exact preregistration and blind commitment; don't rekey it to force a PASS. The coordinator checks source hashes and refuses modifications, but it cannot guarantee science launcher semantics without authentic installed framework/Windows. The above commands launch the original engine and can mutate its runtime output folders: first archive the existing workspace. `FULL` only analyses existing acquired data; it is NOT a 32768 acquisition command.

The latest run's `execution_logs/A058v031-.../NATIVE_STDOUT.log` must remain PRIVATE until checked for blinded mappings. `COORDINATOR_EXECUTION.json` contains exit code and path but no private output. Do not publish acquired private sources or create new scientific claims based on exit code.

## Diagnostics vs experiment changes

User screenshot documents GUI values: charge=15, power=5, hooke=1, spring=1.4, afmpower=2, max-dr=0.1, close=0.12, tinc=15, tanmag=9. The help states `tanf` has an implementation bug; `velfo` scales with velocity and is suitable only in an explicitly Undamped branch. `No Collide` is meant to prevent self-intersections and requires 3D and source-native checks. The old Damped campaign included an anonymous velocity-dependent sector; its null result is not a valid conclusion about Undamped behavior. See `docs/CONTROL_MATRIX.md`.

New commands are handled with isolated scratch probes, with reproducible source scripts and logs; see `docs/COMMANDS.md`. They are NOT injected into the frozen scientific program. To make scientific changes, preregister **A058-v0.4.0**, obtain a new independent blind commitment, implement and run it via the installed framework, and keep all older results byte-identical.
