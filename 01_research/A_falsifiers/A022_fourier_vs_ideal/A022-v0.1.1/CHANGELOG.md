# Changelog

## v0.1.1 — MSVC / Python 3.14 native hotfix

- Replaced POSIX-only unqualified `ssize_t` in `cpp/native.cpp` with `py::ssize_t`.
- Added explicit `<algorithm>` and `<cstdlib>` includes for `std::min`, `std::max`, and `std::llabs`.
- Fixes MSVC 14.44 parse failure during `run_all_extended.cmd`; downstream `unchecked_reference`, `segdist2`, and `vortexlab_velocity` diagnostics were cascade errors.
- No equations, blind thresholds, source matching, campaign logic, or scientific scoring changed.

## v0.1.0

- Added strict matched-pair blinding for `.fseries` vs ideal seeds.
- Added torus-focused and all-common campaigns.
- Added optional `.fseries` vs KnotPlot/RidgeRunner relaxed control.
- Added VortexLab-style local-induction + nonlocal Biot-Savart native C++ kernel.
- Added Kelvin-CFL RK4 integration and no-reconnection contact stop.
- Added SE(3)/cyclic quotient shape drift, curvature high-mode diagnostics, recurrence proxy and transverse restoring-mode Jacobian.
- Added SHA-256 private-key commitment, blind result/code seal and verify-before-reveal.
- Added preregistered sign-test/effect-size post-seal decision rule.
