# Ruban T(2,3) Reproduction Falsifier v0.1.1

**Status:** `DEVELOPMENT_ONLY / PAPER_REPRODUCTION_UNRESOLVED`

## What changed from v0.1.0

1. Implemented a conservative local-induction stability step-size cap, updated at every accepted state. The requested `dt` is now an upper bound rather than a guaranteed step. The cap is a **heuristic**, not full nonlocal stability proof.
2. Check segment regularity on each step and energy/shape criteria at intervals <=0.025 dimensionless time; stop with explicit failure and **exit code 2** on numerical gate failure.
3. Numerical traces save per-run time series and `.npz` 3D snapshots, with a 2x2 **Top / Front / Side / 3D** seed figure, plus an evolution plot in the PDF report.
4. Replaced the bespoke short ReportLab PDF with a **template-aligned TeX report** retaining all 16 official Framework v1.1.0 RC2 science/report section markers, including machine-generated `AUTO_RESULTS.tex`. An authentic snapshot of the retrieved framework template is in `docs/` for audit.
5. Convergence compares runs at a common final time and scales requested `dt` with `N^-2`, while recording any additional cap.
6. Existing input file bytes are untouched, and old output roots are never overwritten.

**Important framework qualification:** This is **not** yet an installed and formally certified SST Framework v1.1.0 RC2 runtime instance. No runtime manifest bootstrap, `FREEZE`, native C++ certification or `REVEAL` was executed. All three special modes refuse to run with exit 4. The authentic framework's `REPORT_CONTRACT.md` is described in `docs/FRAMEWORK_AUDIT.md`.

## Windows local execution

```bat
py -m pip install -r requirements.txt
run_all.cmd TEST
run_all.cmd SMOKE
run_all.cmd BASIC
run_all.cmd CONVERGE
run_all.cmd FULL
```

`FULL` is very computationally expensive (N=256; 7 B0 cases to t=320) and should only be run after successful fixed-time N/dt convergence. You can run a focused canonical trial:

```bat
py -m ruban_falsifier SMOKE --n 256 --dt 0.002 --final-time 1 --snapshot-interval 0.25
```

The step cap automatically reduces the requested time step; review `dt_min_observed` and `min_stability_cap` in `results.json` to distinguish checkpoint clipping from actual step stability. `G2` PASS does not imply long-time stability.

`pdflatex` must be on PATH to produce the template-aligned PDF. If LaTeX is absent, the TeX source, generated AUTO fragments, and plots are retained, but the command signals PDF failure instead of pretending the Framework report was generated.

## Sources / limitations

Based on Ruban (2018), *Long-Lived Quantum Vortex Knots*, arXiv:1801.04822, DOI 10.1134/S0021364018050120, and Ruban (2018), *Quasi-Stable Configurations of Torus Vortex Knots and Links*, DOI 10.1134/S106377611809008X.

Uses analytic T(2,3) filament; `inputs/user_3_1.xyz` is retained for comparison only, **not** evolved as the starting seed. R0=1, Gamma=2*pi. No finite-core Euler, internal twist, dense background field, or physically calibrated tube volume. Colored line weight in plots is not a tube diameter.
