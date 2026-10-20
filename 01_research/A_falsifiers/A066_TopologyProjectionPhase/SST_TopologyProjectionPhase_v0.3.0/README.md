# SST Topology-Projection-Phase Falsifier v0.3.0

**Scientific status:** geometry-library-wide SCREEN + five-family, dimensionless periodic Euler comparative numerical study. **Not** an independently qualified SST particle/stability/reconnection experiment. This is a standalone research implementation derived from v0.2.0; it is **not yet** a native, pinned instance of the frozen SST Falsifier Framework v1.0.7.

## Source corpus (provider-independence contract)

Raw, unchanged source bytes are provided under `external_pklsa/source_libraries/`, and SHA-256 of originals are in `preregistration/UPSTREAM_SOURCES.json`:

- **KnotPlot/Ridgerunner**: real closed trefoil centerline with **300** original points, already in v0.2.0, used as 300 material markers in v0.3.0 Euler.
- **Fremlin Fourier series**: **73** `.fseries` sources. Correct frequency index starts at `j=1` (a `j=0` interpretation falsely unknots the trefoil and figure-eight). An empty coefficient file is marked unresolved, not repaired by guessing.
- **Fremlin `.short`**: **76** additional same-provider polygon exports. These are not independent of the Fremlin Fourier source family.
- **IdealLinks**: **130** link configurations in the Brian Gilbert coefficient archive, with a total of 303 link components. Identical provider mirrors are not counted as independent.

**In total:** 280 configurations and 452 components. Current geometry screening returns 235 `SCREENING_COMPLETE` and 45 `UNRESOLVED_REFINEMENT`. These are not physical-stability pass/fail counts.

## Install and commands (Windows)

Requires Python 3.10+; all commands use local `.venv` and `requirements.txt`.

```bat
run_all.cmd SELFTEST
run_all.cmd CENSUS
run_all.cmd LONG
run_all.cmd ASSESS
run_all.cmd REPORT
```

The `LONG` command executes five selected source geometries at final time `T=2.4`, sigma `0.5`, grids 24, 32, 40 and extra N300 RK4/core regularization refinements. Results appear under `results/EULER_LONG/`; initial setup is not calibrated to physical SST core values.

**Optional whole-library Euler queue:** (potentially many minutes to hours; **not** a substitute for 3-grid testing)

```bat
run_all.cmd EULER_ALL_SCREEN --max-cases 5
run_all.cmd EULER_ALL_SCREEN
```

Every completed source is journaled to `results/EULER_ALL_SCREEN/QUEUE_EVENTS.jsonl`. Re-running with the same parameters skips logged inputs, including recorded unresolved cases; changing parameters creates distinct keys. This command uses single-grid low-resolution Euler and only previously geometry-screened configurations. It may expose CFL failures, bad geometry and overlaps; these are recorded as `UNRESOLVED` rather than converted to successes. Only the **first five** batch cases were exercised during release QA. The entire 235-case Euler queue was **not** completed in this release.

Linux: replace `run_all.cmd` with `./run_all.sh`.

## Mathematical / numerical contract

- 3D incompressible inviscid unforced periodic Euler: `∂_t u = P(u × curl u)`, where P is the Leray projection.
- FFT pseudo-spectral grid, 2/3 de-aliasing, RK4 time stepping, cubic periodic box side `2π`, floating-point Python/NumPy FP64.
- Deposited tangent-vorticity from full closed input curves, Gaussian core `sigma` **in model units**.
- Material marker motion uses trilinear interpolated velocity; marker trajectories are **not independently extracted vorticity ridge centers**.
- Traced 32-point initially-transverse material contours provide approximate Kelvin circulation drift, contaminated by interpolation error; a drift is not a proof of exact Kelvin conservation.
- Topology screen checks Alexander determinant at -1 and Gauss-linking integral; **not** a complete knot classifier. Uniform 96-point arclength resampling is used **only for topology checks**, not for original KnotPlot N300 marker advection.
- All spatial comparisons use **same source, final time, sigma and material IDs**. N300 extra `N=32, steps=192` checks time-step refinement. Varying sigma changes the **physical model**, not its discretization.
- `sigma/h` is only `1.91` at N24, `2.55` at N32 and `3.18` at N40; full core-resolving refinement, independent pressure-Poisson closure and long-time stability are still `UNRESOLVED`.

## Source limitations / reveal integrity

Three original synthetic v0.2 datasets are preserved **byte-identically** and their truth labels remain encrypted. The new library census and Euler numerical studies do not unblind their labels. `results/` includes a reproducible source cross-comparison, not a new blinded physical classifier verdict. Audit/threshold logic developed during v0.3.0 exploration is **retrospective**; it must be independently preregistered and frozen for prospective physical qualification in a later version.

`RUN_LEDGER.json` binds every released result by SHA-256, including the PDF. This is a **local hash manifest**, not independent notarization and not the native v1.0.7 reveal ledger. The canonical v1.0.7 framework remains immutable at Google Drive folder `1IASDEqmcEQXHyTfppetIGgYnVUsvN5hE`. A native certification must be created via its real instance generator, without silent backend fallback.

## Current outcome

| Mechanism | Current result |
|---|---|
| 2D/3D singularity disambiguation | Synthetic v0.2 blind controls maintained |
| Source-independent geometry | KnotPlot, Fremlin, IdealLinks present; same-origin variants labeled |
| Euler topology preservation | Five selected geometries remain within their tested knot/link invariant classes for T=2.4 |
| Spatial marker convergence | Five/5: N32-N40 difference smaller than N24-N32 |
| N300 temporal refinement | RMS path change 3.22467e-7 model length when N32 steps double |
| N300 core width sensitivity | RMS path change 0.0787/0.0849 for sigma 0.4/0.6 relative to 0.5 |
| SST calibrated vortex stability | UNRESOLVED |
| Native framework v1.0.7 certify | UNRESOLVED |

See `results/CONVERGENCE_ASSESSMENT.json` and `results/GEOMETRY_CENSUS.json` for source-level evidence. Run `REPORT` to regenerate the PDF and ZIP.
