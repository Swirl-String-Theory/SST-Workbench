# A050 v0.3.2 — Branch-Retention + Nonstationary Phase Diagnostic

A050 v0.3.2 is a focused post-hoc diagnostic extension of the frozen A050 v0.3.0 real-geometry campaign. It does **not** replace, rescue, or reinterpret the v0.3.0 primary verdict `REAL_GEOMETRY_MODAL_TRANSFER_NOT_REPRODUCED`.

## Why v0.3.2 exists

The frozen v0.3.0 output showed a specific pattern: the five primary baselines and all 25 primary holdouts selected the same recurrent transverse branch label, while the stationary modal-persistence gate failed mainly through long-horizon angular phase-rate variability. At the same time, the inherited temporal-memory, spatial, and divergence gates passed on all five primary baselines.

That observation motivates a narrower question:

> Is branch identity robust under the frozen transverse holdouts even when the phase law is nonstationary, and if so is the phase evolution locally coherent, drifting, or reversing rather than incoherent?

The motivating parent result is frozen in `provenance/PARENT_V030_RESULT_SNAPSHOT.json`, including the parent `blind_results.json` SHA-256. Because this question was chosen after observing v0.3.0, all v0.3.2 conclusions are diagnostic rather than confirmatory.

## Two quantities that v0.3.2 separates

### 1. Branch identity retention

Branch identity is selected from the blind checkpoint dynamics by majority mode with a deterministic low-mode tie break. No numerical mode value is hard-coded as a target.

A branch is called stable when at least 80% of resolved checkpoints select the same mode and at most one checkpoint-to-checkpoint mode switch occurs. A holdout retains the baseline branch when both branch identities are stable and the selected labels agree. This definition is deliberately independent of whether the inherited v0.3.0 stationary persistence gate passes.

A primary base passes the diagnostic retention gate when at least 4/5 holdouts retain its branch. At campaign level, at least 4/5 primary bases must pass and the inherited anonymous source-group minima must also be met.

### 2. Phase evolution of the selected branch

For the dynamically selected branch, v0.3.2 analyses the unwrapped complex-mode phase. The fitted quantity called angular phase rate is

\[
\omega = \frac{d\phi}{dt},
\]

in radians per dimensionless time unit. It is **not** cycle frequency. The corresponding cycle rate is

\[
f=\frac{\omega}{2\pi}.
\]

The diagnostic reports total phase-path length, linear and quadratic fits, BIC preference, eight local angular-rate segments, local phase linearity, piecewise normalized RMSE, and robust angular-rate sign reversals.

The resulting classes are:

- `STATIONARY_COHERENT`;
- `COHERENT_DRIFTING`;
- `COHERENT_REVERSING`;
- `COHERENT_NONSTATIONARY_COMPLEX`;
- `INCOHERENT_OR_UNRESOLVED`.

`COHERENT_REVERSING` is intentionally distinct from incoherence: a continuously evolving phase may pass through \(\omega=0\) and reverse direction while retaining a stable branch identity.

## Diagnostic status logic

The v0.3.2 status is separate from the parent verdict:

- `BRANCH_IDENTITY_NOT_RETAINED` — the recurrent branch label does not survive the perturbation panel;
- `BRANCH_RETAINED_PHASE_INCOHERENT_OR_UNRESOLVED` — branch identity survives, but fewer than 3/5 primary baselines have coherent phase evolution;
- `BRANCH_RETAINED_COHERENT_NONSTATIONARITY_SUPPORTED` — branch retention passes and at least 3/5 primary baselines are coherently drifting, reversing, or otherwise coherently nonstationary;
- `BRANCH_RETAINED_STATIONARY_OR_MIXED_PHASE` — branch retention and phase coherence pass, but coherent nonstationarity is not dominant.

None of these statuses changes the frozen v0.3.0 verdict.

## Runtime scope

v0.3.2 reuses the same frozen external source panel and reruns the 32 staged curves needed for the modal/phase diagnostic: five primary baselines, 25 primary holdouts, and two diagnostic baselines. It does **not** rerun the expensive pressure-grid memory campaign; the v0.3.0 pressure-memory/spatial/divergence results are retained only as cryptographically frozen parent evidence.

## Run

From the `A050-v0.3.2` directory:

```bat
run_all.cmd C:\workspace\projects\SST-Workbench
```

The output is written to `SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.3.2-outputs` and archived as a blind ZIP in the parent directory.
