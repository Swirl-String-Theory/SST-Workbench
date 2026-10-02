# Validation — v0.3.3

Validation date: 2026-09-04.

## Why v0.3.3 exists

The v0.3.2 preregistration specified a periodic-cubic uniform-arclength operator-split remap, but the implementation path used the historical polygonal `np.interp` resampler. v0.3.3 is therefore a corrective software/numerical release rather than a reinterpretation of the v0.3.2 scientific output. The prior v0.3.2 KAtlas smoke remains a negative diagnostic for the implementation that actually ran.

The corrected map uses a periodic `CubicSpline`, dense spline-arclength quadrature, inversion to equally spaced arclength targets, and an exact first-marker cyclic phase anchor. The same remap contract is propagated through S37C, S40, S50 replay, and Phase B.

## Checks completed in this build environment

- Python compile-all: PASS.
- Focused pytest suite: **11 passed**.
- Target-free short dynamic remap benchmark: PASS as a numerical-method diagnostic for the periodic-cubic branch.
- No scientific held-out seed, SST constant target, golden-ratio target, Planck target, or reveal identity is used by the benchmark.
- `require_native=False` is explicit in the local benchmark; this result is not promoted to a held-out physics verdict.

### Short target-free dynamic benchmark

Settings:

- analytic trefoil only;
- resolutions `N = [32, 40, 48]`;
- dimensionless horizon `T_hat = 0.12`;
- remap intervals `[0.06, 0.03, 0.015]`;
- same frozen physical RK4 plan for every cadence at a fixed resolution.

Periodic-cubic branch:

- maximum pairwise cadence-dependent final-shape distance:
  `1.3669306e-3 -> 1.0703347e-3 -> 8.6949255e-4`;
- empirical convergence order: `p = 1.1150651`;
- numerical classifier: `OPERATOR_SPLIT_REMAP_CERTIFIED` on this diagnostic ladder;
- `target_ratio_used = false`.

Legacy polygonal-linear diagnostic branch on the same short ladder also converges (`p = 0.8858062`). This is important: v0.3.3 is not justified by claiming that cubic interpolation numerically dominates every short-horizon test. It is justified by restoring the preregistered operator and making the remap contract explicit and replayable.

The machine-readable result is `validation/remap_kernel_benchmark_short_v0.3.3.json`.

## Scientific gate status

**NOT YET CLOSED BY THIS BUILD SESSION.**

The actual S37C claim requires replay on blind S35 core-robust candidates from the held-out trefoil atlas with the native backend and the configured BASIC/EXTENDED/PRODUCTION ladders. Only an S37C `OPERATOR_SPLIT_REMAP_CERTIFIED` record generated there may admit that candidate to S40. The target-free analytic benchmark above validates the numerical mechanism only.

## Native/backend limitation of this build session

The sandbox lacks `pybind11` and has no package-network access, so the C++ extension could not be rebuilt locally. This is an environment limitation, not a native compile failure. On Windows, `run_00_setup.cmd` installs dependencies and `run_01_build_native.cmd` builds the C++17/pybind11/OpenMP backend before scientific execution.
