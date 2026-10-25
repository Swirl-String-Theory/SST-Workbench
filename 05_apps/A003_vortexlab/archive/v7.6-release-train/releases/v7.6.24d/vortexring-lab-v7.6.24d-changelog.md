# VortexLab v7.6.24d

Base: v7.6.24c / v7.5.3 lineage  
Scope: benchmark orchestration, cyclic-index test correction, selectable knot holdouts, and runtime reduction.  
Solver status: Biot–Savart, filament integrator, topology guard, core model, clock formulas, transfer-law registry, and κ candidates are unchanged.

## 1. Swirl Clock knot selection

A new **TESTKNOOPSELECTIE** block is placed at the top of the CLOCK panel.

- Separate source switches: `ideal` and `fseries`.
- Multi-select knot list:
  - `3₁` → ideal `3:1:1`, fseries `3_1`
  - `4₁` → ideal `4:1:1`, fseries `4_1`
  - `5₁` → ideal `5:1:1`, fseries `5_1`
  - `5₂` → ideal `5:1:2`, fseries `5_2`
  - `6₁` → ideal `6:1:1`, fseries `6_1`
  - `7₁` → ideal `7:1:1`, fseries `7_1`
- The ideal `7:1:1` metadata uses `L/D = 30.700289` with `D = 1`.
- Selection is persisted in local storage.
- The panel shows selected source count, holdout scenario count, snapshot count, and an approximate holdout duration.

### Selection presets

- **Snel:** `3₁`
- **Kernset:** `3₁`, `4₁`, `5₂`
- **Volledig:** `3₁`, `4₁`, `5₁`, `5₂`, `6₁`, `7₁`

Both ideal and fseries are enabled by every preset. The user can subsequently disable either source.

## 2. Split benchmark runners

The former two long runners no longer execute the same 49-snapshot suite.

### Proxy-decompositie

Runs only:

- baseline N=128, five checkpoints;
- static-null N=128, five checkpoints;
- A/B traversal swap N=128, five checkpoints;
- `a_sim = 0.5 mm`, two checkpoints;
- `a_sim = 1.5 mm`, two checkpoints.

Total: **19 snapshots**.

### Continuüm N=128–768

Runs only the trefoil resolution ladder:

- N = 128, 192, 256, 384, 512, 768;
- t = 0 and t = 3 s.

Total: **12 snapshots**.

### Geselecteerde holdouts

Runs only the selected ideal/fseries knot embeddings at N=256 and t = 0, 3 s.

Default Kernset: 6 scenarios / **12 snapshots**.  
Snel: 2 scenarios / **4 snapshots**.  
Volledig: 12 scenarios / **24 snapshots**.

### Volledige confirmatoire suite

Combines:

- 19 proxy snapshots;
- 10 additional continuum snapshots, reusing baseline where possible;
- selected holdout snapshots.

Default Kernset: **41 snapshots**.  
Volledig knot preset: **53 snapshots**.

## 3. In-session result cache

Completed scenario/checkpoint analyses are cached in memory for the current browser session.

- Cache keys include app version, scenario, physical checkpoint time, resolution, `a_sim`, knot source/key, traversal directions, and drift.
- Identical scenarios are reused by later runners.
- Example: a completed proxy baseline can supply the N=128 t=0 and t=3 continuum checkpoints.
- Cache hits are logged as `proxy-decomposition-cache-hit`.
- Exports include cache entry, hit, and computed-snapshot counts.
- No cache is persisted across reloads.

## 4. D4 cyclic-index correction

The v7.6.24c D4 test shifted a discrete curve and then resampled it at new uniform arclength fractions. That operation was not a pure index transformation: it introduced interpolation differences, especially for nonuniform and near-degenerate embeddings.

v7.6.24d tests cyclic invariance using an **exact integer permutation** of:

- centerline points;
- ISO velocity samples;
- mutual velocity samples;
- per-component ordering.

No interpolation or geometric resampling occurs in D4. Segment weights are recomputed from the identically permuted polygon. The gate still tests:

- full intrinsic Ω vector;
- Ω parallel to the intrinsic carrier axis;
- mutual Ω;
- legacy lab-z values as diagnostics only.

A synthetic 257-point nonuniform closed-curve test produced:

- absolute Ω difference: `8.673617379884035e-19`;
- relative Ω difference: `1.0931425659683259e-16`;
- mixed-tolerance score: `1.0931425659545488e-11`.

This validates that the revised D4 operation measures reindexing rather than interpolation sensitivity.

## 5. Mode-aware gates

- D12 is `INFO / not applicable` when a runner does not contain at least four continuum resolutions.
- D13 is `INFO / not applicable` when no holdouts are selected in the current runner.
- D2 and D6 do not fail merely because a holdout-only run contains no applicable legacy phase-proxy snapshots.
- Holdout-only runs report selected-holdout admissibility and embedding-pair sensitivity.
- Continuum-only runs report parameterization convergence, trefoil reach reconstruction, and the continuum audit.
- Proxy-only runs report translation leakage, A/B parity, and the existing negative field-closure result.
- The full confirmatory suite retains the complete R0–R31 research evaluation.

## 6. Visual isolation retained

All automatic runners still temporarily enforce:

- `tracerCount = 0`;
- tracers hidden;
- streamlines hidden;
- potential-flow display hidden.

The previous visual state is restored after completion, manual stop, setup failure, or checkpoint failure.

## 7. RUN menu

The header RUN menu now contains distinct entries for:

- proxy decomposition;
- continuum N128–N768;
- selected knot holdouts;
- full confirmatory suite.

## Validation

- Inline JavaScript syntax: PASS (`node --check`).
- DOM IDs: 443 unique, no duplicates.
- Native `title="Toelichting"`: zero occurrences.
- Version consistency: title, meta, runtime, and footer use v7.6.24d.
- Data availability: ideal `7:1:1` and fseries `7_1` confirmed.
- D4 synthetic exact-permutation test: PASS.
- Diff clean-apply and byte comparison: PASS.
- Solver function hashes for `velocityCore`, `velAll`, `rk4Step`, `acceptedStepTimeCap`, `topologyClearance`, and `topologyStepMayTunnel`: unchanged from v7.6.24c.

A complete interactive WebGL benchmark was not executed in the container because headless Chromium did not terminate reliably. The first local checks should therefore be:

1. **Snel → Geselecteerde holdouts**, expecting 2 scenarios / 4 snapshots.
2. **Continuüm N=128–768**, expecting 6 scenarios / 12 snapshots.
3. Verify D4 no longer fails before running the default 41-snapshot confirmatory suite.
