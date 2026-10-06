# Validation status — A054 v0.1.0

Validated in the artifact environment on 2026-10-06:

- Python reference self-test: PASS.
- Atlas cardinality: PASS (35 knots + 47 links = 82).
- PD traversal/component tests: PASS, including knot, 2-component, 3-component and 4-component cases.
- End-to-end Python reference campaign: PASS (blind -> recursive SHA-256 seal -> seal verification -> reveal -> packaging).
- BLIND leakage scan: PASS for historical topology labels and representative SM/Higgs labels/values.
- Reveal triplet search was optimized with a precomputed centered-log triplet cache; the preregistered score is unchanged.
- C++ source received an MSVC portability check (`constexpr PI`, C++17, pybind11, OpenMP).
- Native compilation was not executable in this artifact environment because `pybind11` is not installed and outbound package installation is unavailable. `run_all.cmd` therefore performs a strict native build and Python/C++ parity test on the target Windows machine before the blind campaign can proceed.

The validation output itself is not bundled in the source archive, so every local run creates a fresh HMAC blind mapping and fresh output seal.
