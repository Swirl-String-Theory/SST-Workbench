# SST Trefoil Dynamic Seed Qualification Mega Falsifier v0.2.0

**Scientific redesign: source-stratified shape discovery + temporal, core, mesh-gauge, long-orbit and mechanism certification.**

The primary question is no longer “is the currently relaxed KnotPlot trefoil stable?” but:

\[
\boxed{\text{Which trefoil start shape most naturally begins as a coherent moving/rolling vortex object?}}
\]

Only after a seed is independently qualified do the stronger orbital and mechanism gates run.

## Hierarchical blind chain

```text
S10 source-stratified trefoil atlas + geometry dedup/contact guard
  -> S20 early rolling-onset screen
  -> S25 blinded local refinement
  -> S30 spatial N=64/96/128 qualification
  -> S32 temporal RK4 convergence
  -> S35 core-radius robustness + champion-cluster classification
  -> S37 low/nominal/high tangential mesh-gauge replay
  -> S40 long free dynamics + symmetry-reduced return search
  -> S50 near-RPO + projected Floquet monodromy
  -> S60 material-core vs fixed-core delayed-stretch causality
  -> S70 reveal
```

A later stage cannot rescue an upstream rejection. Source identity and deformation parameters remain hidden until S70.

## What changed from v0.1.1

### 1. Source-stratified discovery
v0.1.1 BASIC found three unique trefoil source files but its candidate budget could be consumed by variants of the first source. v0.2.0 schedules candidates round-robin across accepted source groups. Base candidates are distributed before deeper variants, and promotion/refinement/qualification stages can enforce a minimum per source group.

Source dedup is geometry-aware after normalized closed-curve cyclic/rigid alignment (`source_dedup_rms_tol = 1e-7` by default), rather than relying on filenames. This directly protects against pseudoreplication by rotated/reindexed/duplicated files.

### 2. POD/QHP are diagnostics, not seed-selection priors
The early score no longer rewards a low POD rank (`pod` weight is frozen to `0.0`). A physically good rolling trefoil may live on a higher-dimensional shape manifold. The ranking is dominated by coherent rigid/rolling motion, symmetry-reduced shape drift, high-k contamination, contact survival and mesh quality.

The rolling fit is

\[
\mathbf u_\perp(s) \approx \mathbf V+\boldsymbol\Omega\times(\mathbf X-\mathbf X_c),
\]

and `rolling_coherence` measures the fraction of normal velocity explained by this rigid component.

### 3. Separate spatial and temporal certification
S30 still tests the frozen spatial ladder. New S32 reruns selected candidates with

\[
\Delta t,\quad \Delta t/2,\quad \Delta t/4
\]

at fixed spatial resolution. A case passes either by an absolute shape-error floor/tolerance or by the preregistered observed convergence order. This prevents “N-convergence” from hiding timestep error.

### 4. Champion **cluster**, not forced winner
S35 reports all candidates inside a preregistered relative score band. A unique champion is declared only if the margin exceeds `unique_champion_min_relative_margin`. This is important because v0.1.1 produced several core-robust shapes separated by only ~10^-3 in score.

### 5. Parameterization-invariant long dynamics
S40 uses a purely tangential segment-length feedback gauge:

\[
\alpha_{i+1}-\alpha_i=-k(\ell_i-\bar\ell),
\qquad
\mathbf u_{\rm mesh}=\alpha_i\hat{\mathbf t}_i.
\]

The RMS mesh speed is capped relative to physical Biot-Savart RMS speed. Shape observables are evaluated after uniform arclength resampling, cyclic parameter-origin alignment, rigid alignment and normal projection, so bead-index drift is not interpreted as physics.

### 6. New S37 mesh-gauge certification
Before S40, each nominated seed is replayed at low/nominal/high mesh-controller strength (default factors 0.6/1.0/1.4). A seed must remain consistent in parameterization-invariant final shape, score and shape-drift AUC. Thus a nominal trajectory cannot become a “stable seed” merely because one tangential gauge happened to behave well.

### 7. RPO status is explicitly epistemic
v0.1.1 stopped all five BASIC champions around `t ~= 0.768` from mesh-quality loss, before the `t >= 0.8` return window. That is **not** a physics result of “no RPO”. v0.2.0 distinguishes:

- `PASS_NEAR_RPO_CANDIDATES`;
- `INDETERMINATE_RPO_WINDOW_NUMERICAL_COVERAGE`;
- `INDETERMINATE_RPO_LONG_HORIZON_COVERAGE`;
- `FAIL_NO_NEAR_RPO_WITH_VALID_COVERAGE`.

A hard no-RPO result is therefore allowed only after sufficient preregistered numerically valid coverage.

A trajectory that later stops may still supply a near-return candidate if the return occurred inside a certified earlier observation interval. Eligibility requires a finite return/time plus the ds-CV, gap and mesh-ratio gates at that return.

### 8. Mechanism remains downstream of existence
S60 may run only on S50 candidates. A material-core predictive effect is insufficient by itself: it must also exceed the fixed-core null by a preregistered margin. The delay is measured from the trajectories; the phase

\[
\phi=\omega_{\rm measured}\tau_{\rm measured}\pmod{2\pi}
\]

is diagnostic output only. No preferred phase or supplied feedback delay enters the dynamics.

## v0.1.1 baseline that motivated v0.2.0

The preceding BASIC campaign found:

- S30: 12/12 resolution-qualified candidates;
- S35: 8/8 core-radius-qualified candidates;
- a tight champion cluster led by `R5571B55051FC0A`, `RBA7D30A2A1971D`, `RBCBB8F3BF914C5` and the unmodified base `CF6A4B99D7EFC81`;
- all five S40 nominees stopped at approximately `t = 0.767--0.769` due to mesh-quality loss before the return window opened.

v0.2.0 therefore treats those shapes as regression targets for numerical certification, not as evidence for or against an RPO.

## One-click Windows runs

Default dataset:

```text
..\..\KnotPlot\knots\final
```

BASIC:

```bat
run_all.cmd
```

EXTENDED:

```bat
run_all_extended.cmd
```

PRODUCTION (freeze config + manifest before use):

```bat
run_all_production.cmd
```

The optional first argument is the dataset directory.

### Individual stages

```bat
run_00_setup.cmd
run_01_build_native.cmd
run_02_selftest.cmd
run_10_prepare.cmd <dataset> <out> <config>
run_20_early.cmd <out> <config>
run_25_refine.cmd <out> <config>
run_30_resolution.cmd <out> <config>
run_32_temporal.cmd <out> <config>
run_35_core.cmd <out> <config>
run_37_mesh_gauge.cmd <out> <config>
run_40_long.cmd <out> <config>
run_50_rpo.cmd <out> <config>
run_60_mechanism.cmd <out> <config>
run_70_reveal.cmd <out>
```

For a **v0.2.0** output tree that already completed S10-S30:

```bat
run_resume_from_32.cmd <output-dir> <config.json>
```

`run_resume_from_50.cmd` is deliberately disabled because v0.2.0 adds mandatory S32/S37 and changes S40 eligibility. Resuming a v0.1.x S40 directly at S50 would bypass the new scientific gates.

## Interpretation guard

This workbench uses a regularized vortex-filament / finite-core surrogate and a projected Floquet subspace. A PASS does not establish full volumetric 3-D Euler orbital stability. Conversely, a hard physics FAIL is emitted only when the relevant numerical coverage gate has itself passed.

See `docs/SCIENTIFIC_PROTOCOL.md` and `docs/CROSS_CAMPAIGN_LESSONS.md`.
