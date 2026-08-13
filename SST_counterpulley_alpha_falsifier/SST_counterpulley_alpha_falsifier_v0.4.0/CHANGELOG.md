# CHANGELOG

## v0.4.0 -- Relative-Periodic-Orbit + True Floquet Monodromy

### Added
- nonlinear dimensionless two-filament time integration;
- geometric normal-flow gauge removing tangential reparametrisation velocity;
- `SE(3)` Kabsch quotient plus common cyclic filament relabelling;
- recurrence and endpoint-vector-field RPO tests;
- preregistered alpha-blind seed scan;
- cross-channel core-overlap termination;
- full-state finite-difference relative return map
  `M = D(g^-1 o phi_T)` for accepted low-N RPOs;
- neutral time-tangent, FD-convergence and real-spectrum checks;
- Kelvin-subspace readout from the true monodromy;
- hard H14 lock: the alpha benchmark remains unopened unless all orbit/Floquet gates pass;
- `run_rpo_search.py/.cmd` and `run_true_floquet.py/.cmd`;
- identity-return unit test for the full monodromy machinery.

### Changed
- v0.3 frozen Kelvin/Floquet generator is no longer accepted as a true Floquet calculation;
- canonical seed H6/H7 are controls; a different preregistered seed can open H8 solely on recurrence quality;
- benchmark runner blocks before importing the numerical alpha target unless H14 passes.

### Reference result
- 11 tests passed;
- native/Python RHS relative error: approximately `2.3e-16`;
- full native H0--H5 PASS;
- H6/H7/H8 FAIL;
- H9--H13 SKIP;
- H14 FAIL;
- alpha benchmark unopened.
