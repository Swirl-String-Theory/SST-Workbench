# Changelog

## v1.0.2 — 2026-10-07

- Fixed C++/pybind compiler provenance: the recorded compiler now comes from the actual setuptools build command instead of the first generic `c++.exe` on `PATH`.
- Added compiler family, compiler version, MSVC toolset, Python ABI and actual compile flags to the native build fingerprint/provenance record.
- Retained the Windows short-object-path hotfix that prevents MSVC C1083 failures from mirrored absolute source paths.
- Retained automatic Intel oneAPI environment activation for SYCL build/link/runtime (`setvars.bat` / `oneapi-vars.bat`).
- Restored the historical SST `sycl-dd32` precision route as DD32 / FP32x2 double-single arithmetic.
- Added `DS{float hi,lo}`, TwoSum/QuickTwoSum addition, FMA-residual multiplication, corrected division, two-step Newton square root and DD accumulation in the SYCL Biot--Savart kernel.
- DD32 keeps coordinates in FP64 transport until the worker-host hi/lo split and recombines `(hi,lo)` to host FP64 only after GPU execution.
- SYCL worker protocol upgraded to v3 with explicit DD32 command and precision metadata.
- SYCL compilation now includes `-fp-model=precise` because DD32 error-free transforms must not be broken by fast-math reassociation.
- Backend selftest expanded to three velocity scenarios plus a deterministic directional finite-difference stress test.
- DD32 acceptance restored from the earlier SST GPU work: velocity relative-L2 <= `1e-8`, directional stress <= `2e-6`, and >= `20x` improvement versus ordinary FP32.
- Added `run_all.cmd DD32` / `run_sycl_dd32_smoke.cmd` and `build/DD32_PARITY_SMOKE.json`.
- DD32 remains `SCREENING_ONLY`: it is not IEEE FP64 and CPU/Python FP64 remain confirmatory/reference lanes.
- Removed all framework/template discovery fallbacks under `04_tools/D_proof`; canonical template discovery is under `06_templates/SST_Falsifier_Framework/`.
- Added DD32 numerical-method documentation and report-template references.

## v1.0.1

- Added strict three-backend numerical parity selftest (`run_02_backend_selftest.cmd`).
- Added deterministic circular and trefoil common-kernel scenarios.
- Python/NumPy FP64 is the reference; C++ FP64 and SYCL FP32/FP64 are compared with explicit relative-L2 tolerances.
- `run_all.cmd ALL` performs setup, framework tests, then backend parity.
- Backend unavailability is a hard failure in the parity test; no silent fallback.

## v1.0.0

- Unified blind/multi-library, C++/pybind11 and SYCL audit infrastructure.
- Immutable create-once protocol freezing with per-file and bundle hashes.
- Gate dependency DAG enforcement; no out-of-order PASS.
- HMAC-SHA256 opaque IDs with private key rather than reversible public-salt hashing.
- Nonced reveal commitments.
- Mandatory blind-tree contamination scan, including `.tex`.
- Strict backend certification: requested/actual backend and authority must match.
- Deterministic output ZIPs and clean-source checks.
- Added human/machine scientific contract and mandatory LaTeX falsifier report.
