# SST Trefoil Dynamic Seed Qualification Mega Falsifier v0.2.1

**Correctness release: evidence-sealed source-diverse discovery with explicit numerical and physics verdicts.**

v0.2.1 preserves the frozen scientific S37 threshold but corrects the v0.2.0 source-selection, status, RPO-contract and causal-language problems documented in `docs/SCIENTIFIC_AUDIT_v0.2.1.md`.

S37 remains `0.035` for BASIC. The previously stricter EXTENDED `0.030` and PRODUCTION `0.025` thresholds are retained, not relaxed. Scientific preparation rejects any threshold above `0.035` and the entire configuration is frozen before scoring.

Scientific BASIC/EXTENDED/PRODUCTION runs now require an explicit fresh held-out dataset path and at least three independent geometry-qualified trefoil source families. The historical `KnotPlot/knots/final` directory is retained for regression only and correctly stops at S10 with `INDETERMINATE_INSUFFICIENT_SOURCE_DIVERSITY`.

The dataset must contain `source_families.json` (see `docs/source_families.example.json`). Each accepted source declares its relative path, family ID, provenance, trefoil topology, single component and held-out status. Multiple shapes from one family count once; missing declarations block scientific promotion. These are auditable declarations, not an automated proof of independence or knot type. Closure/contact checks reject malformed curves but do not replace a topological certificate.

For a non-physical end-to-end code-path check:

```bat
run_all_smoke.cmd
```

Its top-level physics verdict is always `NOT_APPLICABLE_WORKFLOW_VALIDATION`.

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
  -> S60 material-core vs fixed-core delayed-stretch predictive specificity
  -> S70 reveal
```

A later stage cannot rescue an upstream rejection. Source identity and deformation parameters remain hidden until S70.

## What changed from v0.2.0

- full-name trefoil/knot matching rejects `link_*` sources;
- minimum three-family diversity gate for scientific profiles;
- blind keys and identity maps live in a sibling sealed-private bundle until reveal;
- evidence manifest hashes code, configuration, thresholds and dataset files before scoring;
- S30 compares trajectories and final geometries directly across N;
- S32 reports `FLOOR_LIMITED`, `ORDER_CONFIRMED` or `FAILED`;
- S37 zero-qualified status can no longer be mislabeled as mesh certified;
- returns must themselves occur after the frozen observation time and pass local mesh/contact gates;
- S40 and S50 share a hashed discretized dynamics contract;
- S50 freezes S40's actual timestep and guard cadence for the base and every perturbation;
- scoring rejects changed code/config hashes and S10 refuses to overwrite existing evidence;
- public evidence excludes source filenames; reveal fails closed on key, identity-map, geometry or evidence tampering;
- projected Floquet removes resolved neutral directions but remains explicitly projected;
- S60 is a predictive-specificity gate; causal claims remain unauthorized without intervention.

## Foundations retained from v0.2.0

### 1. Source-stratified discovery
v0.1.1 BASIC found three unique trefoil source files but its candidate budget could be consumed by variants of the first source. v0.2.0 schedules candidates round-robin across accepted source groups. Base candidates are distributed before deeper variants, and promotion/refinement/qualification stages can enforce a minimum per source group.

Source dedup uses raw and resampled normalized closed-curve cyclic/rigid alignment, including reversed vertex order (`source_dedup_rms_tol = 1e-7` by default). It protects against rotated/reindexed/duplicated files; family provenance is checked separately.

The sibling sealed-private directory is an operational separation, not encryption or an access-control boundary. The same local user can read it, and recognizable public geometry may reveal identity. Independent blind evaluation requires a separate custodian/process with access only to the public bundle until S70.

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

There is no default scientific dataset. Supply a fresh held-out trefoil atlas explicitly; the scripts refuse to reuse the historical one-source KnotPlot directory as a scientific campaign.

BASIC:

```bat
run_all.cmd <held-out-atlas>
```

EXTENDED:

```bat
run_all_extended.cmd <held-out-atlas>
```

PRODUCTION (freeze config + manifest before use):

```bat
run_all_production.cmd <held-out-atlas>
```

For a non-physical four-source workflow check, use `run_all_smoke.cmd`.

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

For a **v0.2.1** output tree that already completed S10-S30:

```bat
run_resume_from_32.cmd <output-dir> <config.json>
```

`run_resume_from_50.cmd` remains disabled. S50 now also requires the v0.2.1 dynamics-contract hash, so no v0.2.0 S40 tree may be resumed directly.

## Interpretation guard

This workbench uses a regularized vortex-filament / finite-core surrogate and a projected Floquet subspace. A PASS does not establish full volumetric 3-D Euler orbital stability. Conversely, a hard physics FAIL is emitted only when the relevant numerical coverage gate has itself passed.

See `docs/SCIENTIFIC_PROTOCOL.md` and `docs/CROSS_CAMPAIGN_LESSONS.md`.
