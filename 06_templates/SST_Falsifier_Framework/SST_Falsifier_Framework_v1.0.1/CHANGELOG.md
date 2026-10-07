# v1.0.1

- Added strict three-backend numerical parity selftest (`run_02_backend_selftest.cmd`).
- Added two deterministic common-kernel scenarios: circular filament and trefoil filament.
- Python/NumPy FP64 is the reference; C++ FP64 and SYCL FP32/FP64 are compared with explicit relative-L2 tolerances.
- `run_all.cmd ALL` now performs setup, framework tests, then backend parity.
- Backend unavailability is a hard failure in the three-backend test; no silent fallback.

## v1.0.1 backend-build hotfix

Packaging/build fix only; scientific contracts unchanged.

- `native_build.py`: use relative source/package paths and a short `--build-temp` on Windows to avoid MSVC C1083 from absolute-path object trees.
- `sycl_worker.py`: locate/import Intel oneAPI `setvars.bat` / `oneapi-vars.bat` via a temp wrapper `.cmd` (avoids Windows `list2cmdline` quote breakage on `Program Files` paths); use that environment for link **and** worker probe/start so `libmmd.lib` / runtime DLLs resolve; failed builds record compiler/env/LIB diagnostics.
- `sycl_worker.cpp`: add required `template` keyword on dependent SYCL event profiling calls.

# Changelog

## v1.0.1

- Unified blind/multi-library, C++/pybind11 and SYCL audit infrastructure.
- Immutable create-once protocol freezing with per-file and bundle hashes.
- Gate dependency DAG enforcement; no out-of-order PASS.
- HMAC-SHA256 opaque IDs with private key rather than reversible public-salt hashing.
- Nonced reveal commitments.
- Mandatory blind-tree contamination scan, including `.tex`.
- Strict backend certification: requested/actual backend and authority must match.
- Build fingerprint contract includes source, Python ABI, pybind11, compiler identity and flags.
- Deterministic output ZIPs and clean-source checks.
- Added human/machine scientific contract and mandatory LaTeX falsifier report.
- Generated instances start `UNVALIDATED`; template validation never propagates as instance validation.
- External SYCL worker retained as a separate process; GPU FP32 is screening unless an instance explicitly preregisters otherwise.
