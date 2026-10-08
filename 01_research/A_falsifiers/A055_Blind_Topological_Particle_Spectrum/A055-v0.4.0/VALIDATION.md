# A055 v0.4.0 validation

**Release:** A055-v0.4.0  
**Framework:** SST Falsifier Framework **v1.0.4 CANONICAL_FROZEN**  
**Validation date:** 2026-10-07  
**Status:** **IMPLEMENTATION_VALIDATED / PHYSICS NOT ESTABLISHED**

## Canonical framework pin

- framework version: `1.0.4`
- status: `CANONICAL_FROZEN`
- canonical Workbench path: `06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.4`
- canonical framework ZIP SHA-256: `1bdf8a20f0f0cbdf86ab89fb198d1930e0694579dee8d5dcd35149972c0d2104`
- framework package-manifest SHA-256: `1a9e98ee7762ab12746e5327a6552348d5e2edbee8ddaebc557ebaeb261e7452`
- frozen A055 protocol bundle SHA-256: `5e62cad813e92513bf8703d8b3deb173b00a004c1f2bba2ab46176119a8e51b8`

## Static/framework validation

- Python compile: **PASS**.
- framework instance validator: **PASS**.
- A055 public tests: **5 passed, 1 skipped**.
- skipped test: instance-local pybind11 native parity because the release container does not provide pybind11; `run_install.cmd` installs it before the target Windows selftest and G5 is fail-closed.
- SST Falsifier Framework v1.0.4 selftests: **37 passed**.
- public-source blind forbidden-term scan: **PASS**.
- framework reserved-gate audit: **PASS**; G4 remains independent-confirmation/disabled, G5 C++ parity, G6 GPU, G7 cross-source. Representation covariance is part of G2.

## Real A054 implementation smoke

One anonymous A054 compound sector was recomputed without semantic reveal, using the repaired sealed campaign and the NumPy reference backend available in the release container. This is an implementation smoke, not a physical result.

- tested resolutions: `N=56,88`;
- tested Jacobian epsilon values: `0.0025, 0.005`;
- maximum sealed-spectrum assignment-relative error at fine resolution: `4.298937913855639e-15`;
- maximum real-mode metamorphic covariance error: `1.1102230246251565e-16`;
- analytic covariance selftest: **PASS**;
- example sector qualified-mode count / vote bias: `N=56 -> 4 / +1.0`, `N=88 -> 7 / +0.428571...`;
- therefore the example correctly fails the v0.4.0 resolution-stability rule.

This smoke demonstrates that the new gate can distinguish a finest/coarsest directional inconsistency that v0.3.1's finest-resolution-only analysis could not test.

## Scientific boundary

No v0.4.0 FULL physics campaign was executed during release assembly. The package is preregistered and implementation-validated. A physical conclusion requires the user's production `run_all.cmd full` against the canonical Workbench sources.
