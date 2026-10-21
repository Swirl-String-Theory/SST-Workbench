# KnotPlot TANF × Resolution × Iteration Matrix v0.2.0

**Scientific status: DEVELOPMENT / NUMERICAL DIAGNOSTICS.** No KnotPlot runtime has been executed by this package. No Euler, torus-rolling or physical stability result is claimed.

## Design

Two independent knot types (`5_2`, `6_1`), two bead counts (1024, 2048), two matched TANF arms (ON, OFF). Eight requested positive checkpoints, plus baseline iteration zero:
`0, 1, 8, 32, 128, 512, 2048, 8192, 32000`.
Atomic `ago` increments: `1, 7, 24, 96, 384, 1536, 6144, 23808`.

**8 simulation arms and 72 checkpoint snapshots if the full campaign is completed.** Beware that N=2048 and 32000 KnotPlot steps can be computationally expensive. Do not interpret more iterations as automatically more physically correct.

All starts use the same original SmoothClasp v0.2.3 TIGHT seed *within each bead resolution*. The 1024 sources are copied unmodified, and the 2048 sources are regenerated from v0.2.3's dense analytic/interpolated source (not point duplication). Both include the KPT and XYZ for provenance.

KnotPlot settings follow v0.1.1 for reproducibility: `reset all`, `show backdrop`, `mode cb`, `collision fast`, `energy model MD`, `close=0.20`, `max-dr=0.02`, same electrical and mechanical forces, `tanmag=9`, only `tanforce` ON vs OFF differs. `fitto avlength` is excluded to avoid altering geometry scale.

### Stage 1: PILOT — through 512 atomic iterations

In KnotPlot with working directory set to this extracted project root:

```text
read scripts/PILOT/AGO_AB_PILOT_5_2_N1024.kpc
read scripts/PILOT/AGO_AB_PILOT_5_2_N2048.kpc
read scripts/PILOT/AGO_AB_PILOT_6_1_N1024.kpc
read scripts/PILOT/AGO_AB_PILOT_6_1_N2048.kpc
```

**Run these sequentially, not simultaneously.** Each KPC handles one knot and N, first TANF ON then reset/reload and TANF OFF. The `ago` command is atomic, so checkpoints are written after their respective iterations. The scripts intentionally do not invoke `centre` after each step: repeated centering changes stored global motion (and may affect dynamics). KnotPlot GUI may block until each long atomic segment completes.

Then analyze:

```bat
run_analysis.cmd PILOT
```

Inspect `analysis/PILOT/audit.json`, `matrix_long.csv`, `tanf_on_off.csv`, `resolution_1024_2048.csv`, and the PNG graphs. Confirm actual movement, geometric safety, topology at checkpoints, and absence of numerical pathologies. Pilot finishing is **not** automatic clearance for longer runs.

### Stage 2: FULL — through 32000 iterations

**ONLY after pilot qualification.** The FULL scripts deliberately reset to the ORIGINAL KPT and repeat early checkpoints; they do **not** resume from the i00512 `.k` snapshot, because a saved position need not preserve all hidden dynamical state (velocity, memory, thermostat). This is essential for reproducible dynamical comparison.

```text
read scripts/FULL/AGO_AB_FULL_5_2_N1024.kpc
read scripts/FULL/AGO_AB_FULL_5_2_N2048.kpc
read scripts/FULL/AGO_AB_FULL_6_1_N1024.kpc
read scripts/FULL/AGO_AB_FULL_6_1_N2048.kpc
```

```bat
run_analysis.cmd FULL
```

Run output is separated in `checkpoints/PILOT` and `checkpoints/FULL`; rerunning an identical script overwrites its own arm files. Back up outputs before rerunning. A 32000-run stage cannot be stopped mid-`ago 23808` using code-level gates; interruption/manual review is required when anomalies appear.

## Interpretation and methodological limits

* The `tanf` setting modifies numerical filament relaxation, not physical inviscid vortex circulation. The matrix does not measure dynamical stability in Euler flow.
* Equal KnotPlot `ago` iterations at N=1024 and N=2048 are **not** equal physical time; finite-N settings and solver response can vary. Plotting vs iteration is a numerical diagnostic, not continuum temporal convergence.
* 2048 samples are only beneficial if curvature, clearance and knot topology converge as N increases. Higher N can amplify computational cost and alter force/contact scaling.
* The pipeline flags identical sequential XYZ snapshots and missing exports. Indexed RMS includes bead relabeling; Kabsch corrects only overall rigid motions. Resolution comparison resamples the closed polylines to 512 points by arc length and searches for cyclic shifts.
* Static and endpoint checks alone do not prove continuous topological conservation. Pairwise and self-distance checks require a noncrossing certificate across the whole path. `safe`/`dowker` diagnostic outputs should be retained in console logs where possible.
* Geometric self-clearance must be compared to KnotPlot's close threshold and the smallest bending radius; 'looks round' is not a stability certificate.

## Source provenance

Original 1024 seeds from `RoundFolded_NearUnknot_v0.2.3_SMOOTHCLASP.zip` (same SHA-256 retained). New 2048 seeds produced with that release's generator using `build(label,'TIGHT',2048)`. In-package `src/` contains the original v0.2.3 code, `BUILD_MANIFEST.json` contains all source hashes. Nothing is written back to the frozen original releases.

`EXPECTED_MATRIX_72.csv` is a complete planned 72-row design matrix, explicitly marked `NOT_RUN`, not fabricated measurement data.
