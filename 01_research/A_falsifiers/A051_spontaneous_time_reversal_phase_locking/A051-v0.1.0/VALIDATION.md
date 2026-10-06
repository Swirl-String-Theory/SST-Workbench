# Validation plan — A051 v0.1.0

1. Unit-test the gauge invariance and time-odd sign of \(\chi_T\).
2. Unit-test the reversible reference oscillator under the antiunitary map \(\mathcal T:(\phi,p)\mapsto(-\phi,p)\).
3. Run the synthetic reversible branch panel. This is instrument qualification only.
4. Run null controls: single-mode, phase-scrambled, and unlocked/free-phase controls.
5. Run Python/native parity when pybind11 + compiler are available.
6. Audit current upstream readiness. Missing material-phase/core/RPO prerequisites remain explicit `INDETERMINATE`/`SKIP`.
7. A physical campaign is not executed unless an authenticated `TRPL_INPUT_V1` dataset is supplied.

A physical PASS must survive temporal, spatial, finite-core, and geometry/source variation. One-resolution agreement is insufficient.
