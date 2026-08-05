# Changelog

## v0.4.0 — iso-Gamma/A dynamic clock

- Added independent trefoil multipole-phase extraction of `T_dyn`.
- Added matched isolated-run subtraction.
- Added per-run `Q_Gamma` and iso-family spread falsifiers.
- Added fixed-time initial phase-rate gate and strict multi-cycle gate.
- Added solid-body positive control and continuum/discrete representation checks.
- Added C9 configs, analyzer, tests, documentation and Windows batches.
- Validation verdict: bundle-average `Gamma/A` is insufficient for the trefoil phase rate in the frozen hole-contained model.

## v0.3.1 — analyzer schema hotfix

- Fixed `KeyError: intrinsic_residual` when `--input outputs` recursively encountered older campaign summaries.
- Added explicit `--physical-input` and `--numerical-input` arguments.
- Added schema validation and skipped-file reporting.
- Updated Windows batch 23 to analyze only the two intended B6 campaign directories.


## v0.3.0 — axial vortex bundle

Added:

- finite-radius continuum Rankine bundle;
- discrete infinite axial vortex tubes;
- central-hole-derived bundle radius;
- separate `physical_tubes` and `numerical_discretization` modes;
- deterministic near-hexagonal tube placement;
- finite-core Rankine and Rosenhead tube kernels;
- B0–B8 preregistered test configurations;
- circulation-phase clock diagnostics;
- physical/discretization comparison analyzer;
- Windows batches 20–29;
- 11 automated tests;
- smoke outputs and continuum stabilization scan;
- explicit open gate for full 3-D tube backreaction.

Corrected:

- bundle radius is defined as the outer packed-bundle edge; tube centers are placed within `radius - tube_core_radius`;
- physical tube count is no longer treated as a discretization parameter;
- numerical tube circulation is forced to `Gamma_total/N`.

Scientific result:

- fixed-total discrete tubes converge to the continuum Rankine bundle;
- tested frozen hole-matched bundles do not reduce the static trefoil residual below the 5% gate.
