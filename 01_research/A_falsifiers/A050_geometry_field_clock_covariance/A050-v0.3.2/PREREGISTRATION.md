# A050 v0.3.2 preregistration — post-hoc branch-retention / phase diagnostic

## Status

This is a **post-hoc diagnostic** motivated by the frozen A050 v0.3.0 result. The parent verdict `REAL_GEOMETRY_MODAL_TRANSFER_NOT_REPRODUCED` remains immutable. v0.3.2 cannot rescue, replace, or promote that verdict.

The exact motivating parent result is recorded in `provenance/PARENT_V030_RESULT_SNAPSHOT.json` with `blind_results.json` SHA-256 `45039df0f5d30e10c01dfdee5f2a1071ff5a7e1f11c12245bd1956915a4ed4a7`.

## Frozen source rule

Use the same externally staged anonymous v0.3.0 source panel. No synthetic fallback is allowed. Source identity remains reveal-only during dynamics. No mode number is fixed as a target.

## Frozen dynamics

- primary curve samples: 72;
- dimensionless core ratio: 0.1;
- time step: 0.02;
- modal horizon: 2048 steps;
- reparameterization every 2 steps;
- inherited checkpoint set: 320, 640, 1024, 1536, 2048;
- inherited late checkpoints: 640, 1024, 1536, 2048;
- inherited Kelvin candidate range: modes 2 through 8;
- inherited v0.3.0 persistence metrics are computed unchanged for comparison but do not define v0.3.2 branch retention.

## Branch-identity diagnostic

For each carrier, select the reference branch as the majority selected checkpoint mode, breaking ties toward the lowest mode. No numerical mode label is preregistered.

Stable branch identity requires:

- at least 80% of resolved checkpoints on the same selected mode;
- at most one checkpoint-to-checkpoint mode switch.

A holdout retains a baseline branch when both branches are stable and their selected labels agree. The inherited stationary persistence `pass` flag is **not** required.

A primary base passes branch retention when at least 4/5 holdouts retain the baseline branch. Campaign-level branch retention requires:

- at least 4/5 primary bases passing branch retention;
- anonymous source-group minima inherited from v0.3.0: S01 >=2 retained bases, S02 >=1 retained base;
- at least two source groups confirmed.

## Phase-support and local-coherence diagnostic

The dynamically selected branch is analyzed over the full horizon. Samples below 15% of the maximum branch amplitude are excluded from phase fitting. At least 128 active samples and 50% active-sample coverage are required.

The phase uses \(\phi(t)=\operatorname{unwrap}(\arg z(t))\). Report both endpoint displacement and total path length:

\[
N_{\mathrm{net}}=\frac{|\phi(t_f)-\phi(t_0)|}{2\pi},
\qquad
N_{\mathrm{path}}=\frac{1}{2\pi}\sum_i |\Delta\phi_i|.
\]

At least 0.25 total path cycles are required for classification.

The active phase samples are split into eight fixed temporal segments, each requiring at least 64 samples. A segment is locally coherent when its linear phase fit has \(R^2\ge0.55\). Global local coherence requires:

- at least 75% of available segments locally coherent;
- piecewise-linear normalized RMSE <=0.18.

## Phase classes

`STATIONARY_COHERENT` requires local coherence plus:

- global linear \(R^2\ge0.85\);
- segment angular-rate CV <=0.15;
- no significant angular-rate sign reversal.

`COHERENT_DRIFTING` requires local coherence, no significant sign reversal, and:

- quadratic phase \(R^2\ge0.80\);
- quadratic-over-linear \(\Delta\mathrm{BIC}\ge10\);
- quadratic normalized RMSE <=0.25;
- relative start-to-end angular-rate change >=0.25.

`COHERENT_REVERSING` requires local coherence and at least one sign change among significant segment angular rates, with at least four significant-rate segments and both positive and negative segments represented.

A locally coherent trajectory that is neither stationary, simple quadratic drift, nor reversing is classified `COHERENT_NONSTATIONARY_COMPLEX`. All remaining trajectories are `INCOHERENT_OR_UNRESOLVED`.

Angular rate means

\[
\omega=\frac{d\phi}{dt},
\]

in radians per dimensionless time unit. Cycle rate is \(f=\omega/(2\pi)\).

## Campaign diagnostic status

At least 3/5 primary baselines must have a coherent class for phase coherence to be considered present. At least 3/5 must be nonstationary coherent (`COHERENT_DRIFTING`, `COHERENT_REVERSING`, or `COHERENT_NONSTATIONARY_COMPLEX`) for the diagnostic status `BRANCH_RETAINED_COHERENT_NONSTATIONARITY_SUPPORTED`.

These thresholds are frozen for v0.3.2 but are explicitly post-hoc; an independent future panel is required for confirmatory use.

## Explicit exclusions

- no retuning of v0.3.0 acceptance thresholds;
- no replacement of the v0.3.0 primary verdict;
- no hard-coded target mode;
- no source/provider identity available to blind dynamics;
- no absolute SST constants in the blind diagnostic;
- no Floquet/RPO inference;
- no claim that a numerical branch label is a physical Kelvin-wave identification.
