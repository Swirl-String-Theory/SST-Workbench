# Changelog

## v0.4.0-r2 — MSVC native build / fail-closed execution hotfix

- `ssize_t` -> `py::ssize_t` in the pybind11 extension.
- Adds CORE+ELASTIC native parity coverage.
- Repairs CMD errorlevel propagation so failed build/setup cannot continue into FREEZE/run.
- No scientific model, source, threshold, gain-grid, blindness, or gate change.

## v0.4.0-r2 — execution/profile hotfix

- Replaces invalid framework profile `mechanism_injection` with canonical `multilibrary_gpu`; A054-specific mechanism parameters remain instance-local in `configs/mechanism_full.json`.
- Normalizes `%~dp0` before passing the instance root to pip, eliminating the trailing-backslash/quote editable-install failure.
- Splits framework and instance editable installs and checks each return code.
- Propagates non-zero exit codes through setup, run, certification and wrapper scripts.
- No mechanism equations, gains, frozen v0.2 hard gates, discovery geometries, confirmation geometries, or blind mappings were changed.

## v0.4.0
- New framework-v1.0.4 thin instance.
- Freezes the exact v0.2 FULL anonymous geometry cohort as discovery evidence.
- Adds opaque source-native v0.3 KnotPlot link confirmation cohort.
- Introduces BASE/CORE/ELASTIC/CORE+ELASTIC mechanism factorial with global no-refit gains.
- Inherits all v0.2 hard recovery thresholds unchanged.
- Adds independent C++/OpenMP mechanism-kernel certification path.
