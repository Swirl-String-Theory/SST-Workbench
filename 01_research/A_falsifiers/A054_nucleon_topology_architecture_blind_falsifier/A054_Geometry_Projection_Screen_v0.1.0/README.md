# A054 Geometry Projection Screen v0.1.0

**A reproducible stand-alone diagnostic screening** of 50 KnotPlot census geometries, not a new physical SST falsification, certified framework campaign, or A054 v0.5.1 modification. All 50 geometry identities are source labels from KnotPlot, not independently re-certified knot invariants.

## Windows quick start

Run from this extracted package folder:

```cmd
run_all.cmd TEST
run_all.cmd
run_all.cmd FULL
run_all.cmd REPORT
run_all.cmd RESUME
```

- `TEST`: 7 local unit / A054 FP64 parity tests.
- default: 50 source geometries x 2 arms; full Hessian only on frozen pilot (BASIC).
- `FULL`: 50 x 2 arms full reduced Hessian 3-scale sweep, 5 E013 + 2 available relaxed reference overlays, PDF; can take several minutes.
- `REPORT`: re-create only the PDF/Markdown reports from existing FULL data (no physics run), with portable fonts and unique names. Read `results/FULL/REPORT_LATEST.json` for the new filename.
- `RESUME`: reuse pre-existing per-case checkpoints (only when inputs/config/code are unchanged). For a genuinely new run, delete `results/FULL/CHECKPOINTS` or use a different output directory.

## Important distinction

`uniform300_no_relax` is *Python polygonal arc-length resampling*, not the KnotPlot `refine nbeads 300` command. Both arms are passed through A054's frozen 96-total-bead analysis lane. No `ago` is applied by the analysis. The two relaxed examples are separately tagged, never mixed into the 100 primary arms.

A054 v0.5.1 numeric thresholds are retained: Hessian relative matrix error <= 0.25 and stationarity <= 0.1; diagnostic numerical differences are **not** equivalent to scientific FAIL, stability PASS, or E013/A057 admission.

Data coverage: 20 knot labels, 16 link/unlink labels, 14 torus configurations. Twist 11 crossing source is absent; the complete 18-member Knot Atlas link mapping is not independently verified. All 50 source TXT / KPF records are in `inputs/falsifier_census_v0.1.0_output.zip` (TXT also unpacked in `inputs/census/`).

## Main output

- `results/FULL/A054_Geometry_Projection_Screen_v0.1.0__<publication-id>_FALSIFIER_REPORT.pdf` (unique, no overwrite)
- `results/FULL/FALSIFIER_REPORT__<publication-id>.md` (unique); `REPORT_LATEST.json` points to newest pair
- `results/FULL/RUN_SUMMARY.json`, `GATE_LEDGER.json`
- `results/FULL/SCREEN_RESULTS.csv` (100 variants)
- `results/FULL/ROWS.jsonl` (raw numerical diagnostics)
- `results/FULL/CHECKPOINTS/*.json` (restartable results)
- `results/REFERENCE_OVERLAYS.jsonl` (7 historical comparisons)

## Scientific caution

Framework v1.0.7 remains the canonical **external authority**, but its runtime is **not embedded** in this diagnostic package. The 56 canonical framework regressions were **not rerun**. See `FRAMEWORK_NOTICE.json`. For formal state-selection admission, a new frozen framework-pinned A054 instance must qualify stationarity, Hessian convergence, bounded ringdown and independent providers.

## Provenance

Source: the user's Google Drive `Build_Knot_Link_Torus_KnotPlot_Scripts/falsifier_census_v0.1.0_output.zip`. Its exact blob hash, and hashes for all 50 extracted TXT sources, are included. The archived `original_zip_sha256` inside `census_targets.json` refers to another original script archive, not this output ZIP. These identifiers are deliberately not conflated.
