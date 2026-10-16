# A058 v0.3.0 — Real KnotPlot acquisition coordinator

This coordinator does NOT replace the A058-v0.2.9 science engine. It makes a SHA-verified **clone** of the complete original instance. Original results remain untouched; actual acquisition only occurs via the original `run_all.cmd` in the clone on **Windows with the actual KnotPlot executable and original v1.0.8 framework**. Existing v1.0.8 is a locally validated framework candidate, not automatically the `v1.0.7-CANONICAL_FROZEN` release.

Prerequisite: original entire `A058-v0.2.9` folder and framework v1.0.8 already installed on Windows with working KnotPlot. No `KnotPlot.exe` or E011 source data are bundled. The source itself must pass its install/runtime qualification.

From this directory:
```
run_all.cmd SELFTEST
run_all.cmd TRIAGE --analysis "C:\path\A058_SLIDER_ANALYSIS.json" --ledger "C:\path\GATE_LEDGER.json" --runlog "C:\path\campaign\runs\BASIC\runlog.json"
run_all.cmd PREPARE --source "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A058_KnotPlot_Parameter_Sensitivity_Relaxation_Robustness\A058-v0.2.9"
run_all.cmd STATUS
run_all.cmd INSTALL
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd 2048
run_all.cmd 32768
run_all.cmd FULL
run_all.cmd STATUS
```

`PREPARE` rejects existing acquisition workspaces rather than overwriting. It preserves existing private commitment files *locally* within the cloned instance, so this is a continuation under the original frozen protocol, **not** a new blind randomization. Never publish `acquisition_workspace/` or its private files. `FREEZE` invokes the **unmodified** source launcher and must verify the preserved existing valid blind commitment; if copied preregistration/private state prevents successful commitment verification, stop and repair source by new version — do not rekey a frozen instance. `BASIC` runs 271 equal-budget conditions to 512 iterations; `2048` repeats 271 to 2048 iterations; `32768` selects at most 31 cases, no lookahead. Exact checkpoints are frozen as `[32,128,512]`, `[32,128,512,2048]`, and `[32,128,512,2048,8192,32768]`.

**Do not use `FULL` to acquire the 32768 cases**: original FULL analyzes the current acquired run only. Do not infer an attractor or asymptotic stability from finite-budget matched-iteration responses. Inspect original raw KnotPlot stdout, saved centerlines, per-sector eligibility, state-reset effectiveness, runtime verification, and official scientific gate ledger. `UNSUPPORTED_RUNTIME` is neither physics FAIL nor PASS.

The coordinator selftest runs in any OS and uses a fake config. It NEVER simulates actual KnotPlot acquisition. The Windows commands above are required for real data.

## Update from the actual 2026-10-13 A058 BASIC results
The source v0.2.9 BASIC tier was subsequently executed: 271 recorded conditions, 177 runtime failures, 34 unsupported, G1 FAIL, G2 FAIL, G8 FAIL, G3 PASS, G5 PASS; parameter-state verification 34.69%, coordinate completeness 87.45%. Therefore start with `TRIAGE` and repair state readback/export/runtime compatibility **before** a full 2048 campaign. The coordinator intentionally does not alter original runner's scientific protocol; implementation patches to KnotPlot subprocess/controller will need a separately reviewed source-engine version once real private logs identify root causes.
