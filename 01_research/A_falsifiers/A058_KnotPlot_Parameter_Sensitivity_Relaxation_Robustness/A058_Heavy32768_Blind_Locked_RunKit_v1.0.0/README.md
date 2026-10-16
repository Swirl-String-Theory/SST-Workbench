# A058 BLIND 32768 — locked selection RunKit v1.0.0

**Source:** A058-v0.2.10, SST Falsifier Framework v1.0.8. This is a **detached selection and launch tool**, **not** a change to the frozen experiment or a replacement falsifier version.

## Scientific decision (recorded before the heavy run)

Exactly **27 of 271** conditions were selected from the valid 2048-iteration BLIND outcomes:

- 5 valid sector references (`C0000`, `C0001`, `C0002`, `C0003`, `C0005`)
- 1 sector activation control (`C0006`)
- 3 response conditions for each of S0, S1, S2, S3, S4, S5, and S7 (21 total)
- R4/S6 are excluded as `UNSUPPORTED_RUNTIME`, **never** interpreted as zero response.

The algorithm is **exactly** `tools/run_budget.py::heavy_selection` from v0.2.10: highest local response near the reference, maximum observed combined shape/scalar response, and zero/endpoint robustness diagnostic (with documented deterministic de-duplication). The full condition-ID list, multiplier, score, rationale and source hashes are in `HEAVY_SELECTION_LOCK.json` and `SELECTED_32768.csv`. Only anonymous axis IDs are used here.

**No heavy outcomes were inspected or used to make this decision.** Selection is *conditional on observed 2048 data*, not a new independent confirmatory dataset. It still provides a blind, preregistered next-stage test.

## Prepare and run (Windows)

Unzip this RunKit **beside** the existing `A058-v0.2.10` instance. Do not move the complete original `campaign/runs/2048` or `private/install_test_runtime` folder: the runner requires both.

From Command Prompt inside this RunKit:

```cmd
run_32768_locked.cmd "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A058_KnotPlot_Parameter_Sensitivity_Relaxation_Robustness\A058-v0.2.10" CHECK_ONLY
```

When `CHECK PASS` confirms the **27 exact IDs**, run:

```cmd
run_32768_locked.cmd "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A058_KnotPlot_Parameter_Sensitivity_Relaxation_Robustness\A058-v0.2.10"
```

The first command checks the lock and does **not** run KnotPlot. The second runs the original `run_all.cmd 32768` with no changes to code, protocol, BLIND output or prior 512/2048 runs. It re-verifies the selected conditions against the locked selection after completion.

The kit requires the existing `.venv` in A058-v0.2.10 and the original KnotPlot executable at the same installation path. It fails closed if the executable, seed, source code, 2048 runlog, any of the 237 valid final geometries, or selector outcome changes. It refuses a second heavy run if a `campaign/runs/32768` directory already exists; use `locked_heavy.py VERIFY` instead.

## Budget, scope and safety

- Checkpoints **32, 128, 512, 2048, 8192, 32768**; increments sum to 32,768 per case.
- Planned maximum **27 x 32,768 = 884,736** KnotPlot `go` iterations, plus sector preflights.
- The heavy tier repeats from the **same safe initial trefoil seed**, not from the 2048 final geometry. This is necessary for matched time horizons.
- A058-v0.2.10 verifies condition start/end safety; it does **not** certify safety at *every* intermediate checkpoint. Do not interpret the heavy results as continuous topological preservation or proof of convergence.
- The results remain **BLIND**. Do not run `REVEAL_IF_ALLOWED` until the heavy results and audit are archived.
- The official G0-G9 BLIND gate statuses (including missing S6 coverage) are not overwritten or upgraded by this detached tool.

## Contents and verification

- `HEAVY_SELECTION_LOCK.json`: sealed decision, source runlog/manifest/runtime/summary hashes, hashes of all 237 valid 2048 final geometries, exact selected IDs and scores.
- `HEAVY_SELECTION_LOCK.sha256`: self-checksum for the decision.
- `SELECTION_ENGINE_EXPECTED.json`: exact native selector output, verified against re-execution.
- `SELECTED_32768.csv`: readable 27-condition shortlist.
- `locked_heavy.py`: fail-closed independent pre/post audit; **no** edits to the frozen v0.2.10 instance.
- `run_32768_locked.cmd`: check-only or verify-then-launch runner.
- `VALIDATION.md`: local tests and limitations.

**Lock SHA-256:** `11c0bb20703a8bcc7c0565620a485131a6feb36d649f21516c84f6b59be37137`.
