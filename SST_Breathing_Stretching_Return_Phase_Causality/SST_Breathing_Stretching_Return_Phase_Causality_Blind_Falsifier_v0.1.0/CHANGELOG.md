# Changelog

## 0.1.1 — 2026-08-27

- **Windows/MSVC build fix:** replace every unqualified `ssize_t` in `cpp/native.cpp` with `py::ssize_t`.
- Fixes the first MSVC parser failure at `native.cpp:18` (`C4430` / `C2146`) and the subsequent OpenMP/parser error cascade.
- Adds a regression test that rejects future bare `ssize_t` in the pybind11 native kernel.
- No changes to equations, dynamics, blind protocol, scoring gates, configs, or default dataset.

## 0.1.0 — 2026-08-27

- First Breathing–Stretching–Return-Phase Causality release.
- Anonymous matched ripple-polarity arms with semantic reveal separated from scoring.
- Regularized Biot–Savart RK4 evolution in C++/pybind11/OpenMP with Python audit kernel.
- Material line-stretch observable from segment extension rate.
- Primary material-core closure: per-segment `a^2 * ell = const`, with `a_j(t)` fed back into every RK4 Biot–Savart evaluation.
- Fixed-core (`core_length_exponent = 0`) extended null and explicit stretch-mediation comparison gate.
- Differential stretch-packet tracking by circular cross-correlation.
- Return time measured from one full unwrapped material-coordinate circuit.
- Coherent breathing phase from a refined harmonic fit, with propagated coefficient/frequency/return-time phase uncertainty; no target phase is supplied.
- Post-return restoring-response score plus pre-return nonlocal-contamination guard.
- Half-return and three-quarter-return temporal-null circular models; primary return model must outperform them.
- Matched N=64/96/128 resolution ladder with a frozen convergence summary.
- Carrier-held-out circular regression and carrier-grouped permutation test.
- Fixed-time, dt proportional to ds^2 integration discipline.
- BASIC, EXTENDED, resolution, selftest, and separate reveal commands.
