# Validation — Maxwell–SST Kinetic Falsifier v0.1.0

Validated in the active runtime with Python 3.13.5.

## Automated checks

- `python -m compileall -q src`: PASS
- `pytest`: **9 passed**
- synthetic non-failing demonstration: `DEMO_ONLY`, 0 physical failures, 0 numerical/closure failures
- synthetic intentionally failing demonstration: `DEMO_ONLY`, 3 physical failures, 5 numerical/closure failures

The intentionally failing dataset exercises:

- positive-gap claim contradicted by an `A -> 0` continuous energy branch;
- thermodynamic mode-count violation;
- spectroscopic bound violation;
- resolution non-convergence;
- energy-ledger drift;
- twist-without-material-frame guard;
- writhe double-count guard;
- core-mode-without-finite-core guard.

## Numerical SST scale checks

Using the declared canonical values in `constants.py`:

- `0.5 * rho_f * v_swirl^2 = 418774.3917945338 Pa`
- `v_swirl / r_c = 7.763440655383073e20 s^-1`

These are intentionally labeled scale checks and are never used as an inferred knot-gas pressure or as an internal-mode gap.

## Scientific scope limitation

v0.1.0 does not derive the mode basis, Hessian, generalized inertia, finite-core eigenmodes, physical encounter kernel or empirical spectroscopy limits. It audits such inputs once supplied. A real falsification campaign therefore requires solver- or experiment-derived physical input with thresholds frozen before held-out comparison.
