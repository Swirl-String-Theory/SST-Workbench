# Changelog

## 0.2.1

- Fixed the `L2a1` recursion overflow with iterative disjoint-set path compression.
- Added symmetric mutual-contact sampling and explicit double-critical self-contact candidates.
- Added contact-patch clustering, an augmented contact graph and directed contact-map orbit detection.
- Added period histograms and candidate period-9 diagnostics with a strict non-billiard guard.
- Added bounded local refinement of Fourier curvature maxima.
- Made `comparison_epsilon_D=0.1` the primary cross-link dynamical gate.
- Demoted minimum-over-epsilon ranking to a smoothing-sensitivity diagnostic.
- Added exploratory epsilon-squared extrapolation to `epsilon -> 0`.
- Added Ridgerunner OOGL VECT export, round-trip validation and provenance manifest.
- Added `rebuild-report` so combined tables can be reconstructed from per-link JSON ledgers.
- Added a Windows process-isolated production runner with resume and retry support.
- Changed launchers to use the project virtual environment rather than bypassing it with `py -3`.
- Added regression tests for long contact chains, Hopf continuous contact, curvature refinement and
  VECT round-trip fidelity.

## 0.2.0

- Added native C++17/pybind11 Biot–Savart, Gauss-linking and Neumann kernels.
- Added strict native/Python parity and backend provenance.
