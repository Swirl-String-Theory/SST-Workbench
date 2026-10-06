# A050 v0.4.0 — Phase-Reversal Mechanism Discrimination

A050 v0.4.0 follows the v0.3.2 result `BRANCH_RETAINED_COHERENT_NONSTATIONARITY_SUPPORTED`. The frozen v0.3.0 verdict and v0.3.2 diagnostic status remain immutable.

## Better hypothesis

The selected transverse branch is not well described by a single constant angular phase rate. Instead its phase obeys

\[
\phi(t)=\phi_0+\int_0^t \omega(t')\,dt',
\]

where the observed drift/reversals arise from one or more low-dimensional mechanisms. v0.4.0 discriminates five candidate mechanisms rather than treating all nonstationarity as one class:

1. `SMOOTH_CHIRP`: coherent monotone acceleration/deceleration of phase;
2. `TWO_TONE_BEATING`: interference of two coherent complex-frequency components, predicting envelope modulation and reversal clustering near amplitude minima;
3. `PHASE_SLIP`: abrupt phase increments concentrated at low-amplitude events;
4. `RPO_CANDIDATE`: recurrence of the symmetry-reduced modal state with a reproducible group-phase advance;
5. `AMPLITUDE_PHASE_MODULATION`: reproducible coupling between branch amplitude and angular phase rate after simple beating/slip signatures are excluded.

Multiple signatures may coexist; `MIXED_MECHANISM_SIGNATURE` is therefore an allowed carrier-level result.

## Critical change from v0.3.2

v0.3.2 was post-hoc on the original five holdout sets. v0.4.0 freezes the mechanism tests first and generates a **new deterministic holdout panel** from the same five external baselines using a new seed. A mechanism is campaign-supported only when it is present on a baseline, replicates in at least 4/5 fresh branch-retaining holdouts for that base, appears on at least 3/5 primary bases, and satisfies the anonymous source-group minima.

This is prospective perturbation replication, not a new-provider confirmation.

## Symmetry-reduced recurrence

For modal coefficient \(C_m(t)\), the spatial phase action is quotiented as

\[
C_m(t)\mapsto C_m(t)e^{-im\theta(t)},\qquad
\theta(t)=\frac{\arg C_{m_0}(t)}{m_0},
\]

where \(m_0\) is the dynamically selected reference branch. Recurrence is assessed in this quotient state. This is stronger than simply subtracting the same complex phase from every mode.

An `RPO_CANDIDATE` does **not** activate Floquet analysis. A later version must first solve and numerically converge an actual relative periodic orbit.

## Run

```bat
run_all.cmd C:\workspace\projects\SST-Workbench
```

Primary outputs include `blind_results.json`, `mechanism_carriers.csv`, `mechanism_bases.csv`, `mechanism_summary.csv`, and `BLIND_RUN_REPORT.md`.
