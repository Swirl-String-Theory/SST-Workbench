# Validation status — v0.2.1

Execution-only patch over v0.2.0. Scientific configs, blind salts, gates, frozen seeds, and thresholds are unchanged.

Validated in this release build:

- [x] Python unit tests.
- [x] Non-destructive output-directory allocation test.
- [x] Non-destructive archive-path allocation test.
- [x] Repeated smoke packaging preserved the first BLIND/REVEALED ZIPs and emitted run-suffixed archives.
- [x] Python smoke campaign with BLIND and REVEALED packaging.
- [x] Frozen input SHA-256 gate.
- [x] Blind source leakage audit.
- [x] v0.2.0 -> v0.2.1 Python smoke scientific-summary parity.
- [ ] Native C++17/pybind11 + OpenMP rebuild independently rerun for v0.2.1. Native source/model code is unchanged except the backend docstring version.
- [ ] Python/native parity campaign.
- [ ] Basic four-seed campaign.
- [ ] Extended finite-core ladder campaign.
- [ ] PKLSA exported centerline added as an independent geometry arm.
- [ ] Certified RPO supplied upstream before any Floquet multipliers are evaluated.

The user-provided v0.2.0 Windows log reached a successful MSVC/OpenMP compile, link, and `.pyd` copy before the old destructive output cleanup failed. v0.2.1 specifically removes that cleanup failure mode.
