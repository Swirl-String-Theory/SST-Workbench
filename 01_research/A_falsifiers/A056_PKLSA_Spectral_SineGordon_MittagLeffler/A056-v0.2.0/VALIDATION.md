# Validation — A056 v0.2.0 / SST Falsifier Framework v1.0.0.dev0

Validation date: 2026-10-06.

## Framework regression test

The bundled development snapshot was exercised as the first A056 consumer.

- `pytest`: **5 passed**.
- framework/science self-test: **PASS**.
- Mittag--Leffler exponential limit: maximum absolute error `1.1102230246251565e-16` for \(E_{1,1}(-t/2)=e^{-t/2}\).
- blind scientific-source scan: **PASS**, zero forbidden reveal markers in `a056_falsifier/` or `sst_falsifier_framework/`.
- synthetic dynamic-provider population: 5/5 provider contracts admissible.
- reveal regression: **IMPLEMENTATION_VALIDATED**, 5/5 phase classes and 5/5 ringdown classes selected correctly.

## Framework-smoke gate result

The smoke profile intentionally permits absence of the optional pybind11 extension so that the framework control suite can run in a restricted environment. Gate results were:

`G0 PASS -> G1 PASS -> G2 PASS -> G3 PASS -> G4 PASS -> G5 PASS -> G6 PASS`.

All four confirmed candidate cases passed candidate-specific deterministic numerical certification in the framework-smoke profile. The two synthetic cases carrying both injected Sine--Gordon and Mittag--Leffler structure (`SYNTH_A`, `SYNTH_E`) remained certified; the memory-only `SYNTH_C` control is now certified by the Mittag--Leffler convergence lane rather than being incorrectly judged by Sine--Gordon coefficient convergence. The synthetic blind conclusion was `JOINT_SUPPORTED`. That conclusion is an implementation-control result only.

## Production fail-closed check

The same synthetic population was also run with `configs/basic.json`, where `native_required=true`. The current container does not provide pybind11 headers and has no network access to install them. The production chain therefore correctly stopped at:

`G4_NUMERICAL_CERTIFICATION = UNRESOLVED`,
`G5_CROSS_SOURCE_REPLICATION = NOT_RUN_PREREQUISITE`,
`G6_MECHANISM_PHYSICS = NOT_RUN_PREREQUISITE`.

This is the desired framework behavior: a successful model fit cannot be promoted past a missing required numerical-certification backend.

## C++ / SYCL status in this validation environment

`cpp/native.cpp` and the setup/build path are included but the native module could not be compiled here because pybind11 is unavailable offline. On the Workbench machine, `run_install.cmd` installs pybind11, builds C++17/OpenMP, and retries serial C++ if OpenMP fails.

The oneAPI/SYCL worker is an optional out-of-process architecture probe. It was not executed in this Linux container. On the Arc A770 Workbench machine use `run_35_sycl_worker_smoke.cmd`; it sets `ONEAPI_DEVICE_SELECTOR=level_zero:gpu` and `SYCL_CACHE_PERSISTENT=0` for that process.

## Real-data status

No real PKLSA/Euler/finite-core dynamic provider was supplied to this validation. Therefore v0.2.0 makes **no SST physics claim**. `run_real_blind.cmd` is ready to ingest a provider that freezes `phase_definition_id`, perturbation, solver/provider version, carrier SHA-256, upstream geometry SHA-256, and independent source group.
