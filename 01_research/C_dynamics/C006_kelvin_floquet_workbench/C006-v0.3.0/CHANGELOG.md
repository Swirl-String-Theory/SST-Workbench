# Changelog

## v0.3.0 — 2026-09-25 — spectral certification + Darboux eligibility

Copy-on-write scientific extension from C006-v0.2.2.

- Preserves K0–K14 semantics and the hard `NO_RPO => NO_TRUE_FLOQUET` rule.
- Adds Phase V, K15–K20.
- Adds frozen target-blind spectral thresholds in `SPECTRAL_THRESHOLDS_FROZEN.json`.
- K15: stable-root tracking across trefoil resolution; generic QEP linearization self-test.
- K16: regularized-core parameter continuation, branch non-monotonicity and descriptive non-oscillatory-mode census.
- K17: conjugate/quartet spectral symmetry-defect diagnostics.
- K18: synthetic Darboux factorization self-test plus finite-dimensional common/differential-sector intertwining pretest.
- K19: strict SST Darboux gate; intentionally `SKIP` without two independently derived scalar second-order SST operators.
- K20: frozen-local spectrum to true relative-Floquet cross-certification; intentionally locked behind K6.
- Adds `run_phase5.py` and `run_phase5.cmd`.
- Updates `run_all.py` / `run_all.cmd` to five scientific phases.
- Adds focused v0.3.0 unit tests and source-to-SST method-bridge documentation.

No Gauss–Bonnet dynamics, black-hole QNM boundary conditions, external target values, or post-run threshold retuning are introduced.
