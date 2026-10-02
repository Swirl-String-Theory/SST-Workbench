# v0.4.8 Adaptive High-k DD32 Spectral Convergence Extension

## Purpose

v0.4.7 localized the main remaining resolution uncertainty to spectral truncation: spatial refinement at N=720 was substantially better behaved than the k_max=8/12/16 tail. v0.4.8 therefore holds the centerline resolution fixed at N=720 and extends only the reduced Kelvin/TBK spectral basis.

## Preregistered ladder

The baseline is the v0.4.7 linear rung `R4_N720_K16_SPECTRAL`. It may be imported from either the original output directory or its ZIP archive. Input SHA-256, N=720, k_max=16 and epsilon_ref=0.004 are checked before reuse.

| stage | N | k_max | execution |
|---|---:|---:|---|
| S0 | 720 | 16 | reuse v0.4.7 R4 if available; otherwise recompute |
| S1 | 720 | 24 | mandatory, linear-only |
| S2 | 720 | 32 | mandatory, linear-only |
| S3 | 720 | 48 | only for unresolved datasets |
| S4 | 720 | 64 | only for datasets still unresolved |

Every new rung uses epsilon = {0.001,0.002,0.004,0.008} and the comparison Jacobian is always epsilon_ref=0.004. Ringdown, RPO and Floquet are deliberately not repeated at each spectral rung. The v0.4.8 spectral fast path still computes all four full reduced Jacobians, but performs only one dense eigendecomposition on the epsilon=0.004 reference matrix and skips family-ablation work that is irrelevant to the spectral closure decision.

## Adaptive stop rule

At k=32 the tail is evaluated on (16,24,32); at k=48 on (24,32,48); at k=64 on (32,48,64).

A dataset may stop as `SPECTRAL_CONVERGED_K*` only when all of the following hold:

1. Growth tail is quasi-monotone.
2. `|Delta_last| / |Delta_previous| <= 0.75`.
3. Last relative growth change is <= 0.03, scaled by `max(|g_last|, 0.12)`.
4. P2 (`g <= 0.12`) is unchanged across all three tail points.
5. The requested k_max basis survives rigid-mode removal and orthonormalization.
6. Dominant-mode exact-boundary weight at k_max is <= 0.10.
7. If Kelvin-family weight is >= 0.05, the fraction of Kelvin eigenmode energy in the upper quarter `k >= ceil(0.75 k_max)` is <= 0.05.
8. Requested k_max is <= 0.75 of the Nyquist limit of the least-sampled component.
9. The uncertainty proxy from the measured final step and diagnostic power-tail fit does not overlap g=0.12.

The diagnostic fit

`g(k_max) = g_inf + c k_max^(-p)`

uses `0.25 <= p <= 6`, but the fit can never establish convergence without the measured-tail conditions above.

A dataset still failing any condition at k_max=64 is reported as `SPECTRAL_UNRESOLVED_AT_K64`. This is an intended falsifier outcome, not a software failure.

## Mode-spectrum diagnostics

Each dominant eigenmode already records `kelvin_k_weight`. v0.4.8 derives:

- exact k_max boundary weight;
- total Kelvin-family weight;
- high-k cutoff `ceil(0.75 k_max)`;
- absolute high-k weight;
- high-k fraction within the Kelvin family;
- component point counts, least-component Nyquist k, and k_max/Nyquist fraction.

This prevents an apparently stable growth scalar from being accepted when its eigenvector is still concentrated at the spectral truncation boundary.

## Cost scaling and mode counts

For one component the requested basis contains approximately:

| k_max | reduced modes |
|---:|---:|
| 16 | 63 |
| 24 | 95 |
| 32 | 127 |
| 48 | 191 |
| 64 | 255 |

Multi-component systems scale approximately with component count, so a three-component k=64 case can approach 765 reduced modes. This is why adaptive stopping and the single-reference-eigendecomposition fast path are important. In the completed v0.4.7 archive the least-sampled normalized component had 190 points, giving Nyquist k=95; k=64 therefore reaches about 0.674 of that worst-case Nyquist limit and remains below the preregistered 0.75 guard.

## Commands

Optionally validate the previous large v0.4.7 output first:

```bat
run_spectral_extension_baseline_check.cmd "C:\path\to\outputs_hr_ladder_dd32_..."
```

Then reuse it directly:

```bat
run_spectral_extension_dd32.cmd "C:\path\to\outputs_hr_ladder_dd32_YYYYMMDD_HHMMSS_mmm"
```

or its ZIP:

```bat
run_spectral_extension_dd32.cmd "C:\path\to\outputs_hr_ladder_dd32_YYYYMMDD_HHMMSS_mmm.zip"
```

A second argument overrides the output directory.

If no baseline argument is supplied, the runner searches the current project and sibling version directories for the newest `outputs_hr_ladder_dd32_*`. If none is found, S0 K16 is recomputed.

Resume by reusing the same output directory:

```bat
run_spectral_extension_resume_dd32.cmd outputs_spectral_extension_dd32_... "C:\path\to\v0.4.7_baseline"
```

Sequential sharding is available for fault isolation:

```bat
run_spectral_extension_dd32_shard.cmd 8 0 "C:\path\to\baseline" outputs_spectral_shard_0
...
run_spectral_extension_dd32_shard.cmd 8 7 "C:\path\to\baseline" outputs_spectral_shard_7
run_spectral_extension_merge_shards.cmd outputs_spectral_merged outputs_spectral_shard_0 outputs_spectral_shard_1 outputs_spectral_shard_2 outputs_spectral_shard_3 outputs_spectral_shard_4 outputs_spectral_shard_5 outputs_spectral_shard_6 outputs_spectral_shard_7
```

Do not run multiple shards concurrently on one Arc GPU unless intentionally benchmarking contention.

## Outputs

- `SPECTRAL_EXTENSION_RESULTS.json`
- `SPECTRAL_EXTENSION_SUMMARY.csv`
- `SPECTRAL_EXTENSION_CONCLUSIONS.md`
- `SPECTRAL_UNRESOLVED_QUEUE.json`
- `CPU_FP64_CONFIRMATION_QUEUE.json`
- `SPECTRAL_EXTENSION_PLAN_PREREGISTERED.json`
- `BASELINE_SOURCE.txt`
- per-stage active-source ledgers and normal blind campaign outputs

DD32 remains FP32x2 rather than IEEE binary64. The prior 127-object campaign parity supports its use as the high-precision accelerator for this ladder; CPU/OpenMP FP64 remains the independent reference audit for converged PASSes and threshold-sensitive cases.
