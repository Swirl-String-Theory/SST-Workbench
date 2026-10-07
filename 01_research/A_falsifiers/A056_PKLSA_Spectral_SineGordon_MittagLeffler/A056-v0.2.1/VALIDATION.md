# Validation — A056 v0.2.1 / SST Falsifier Framework v1.0.2-dev

Validation date: 2026-10-07.

## Local framework/science regression

The package was exercised in the available Linux validation environment.

- `pytest`: **13 passed**.
- framework/science self-test: **PASS**.
- exact framework-root locator: **PASS**.
- deterministic build-fingerprint regression: **PASS**.
- Gate-5 synthetic pseudo-replication regression: **PASS**.
- Mittag--Leffler exponential limit: maximum absolute error `1.1102230246251565e-16` for \(E_{1,1}(-t/2)=e^{-t/2}\).
- blind source-tree scan: no reveal terms in the scientific/framework source tree.
- synthetic provider population: 5/5 admissible after adding `evidence_class=synthetic_control`.

## Framework-smoke result

The smoke profile intentionally allows absence of the native extension in this restricted environment.  The five-case synthetic campaign produced:

```text
G0_PROVENANCE                 PASS
G1_ADMISSIBILITY              PASS
G2_DISCOVERY                  PASS
G3_CONFIRMATION               PASS
G4_NUMERICAL_CERTIFICATION    PASS
G5_CONTROL_REPLICATION        PASS
G5_CROSS_SOURCE_REPLICATION   NOT_RUN_PREREQUISITE
G6_MECHANISM_PHYSICS          NOT_RUN_PREREQUISITE
```

Blind conclusion:

```text
JOINT_CONTROL_RECOVERED
```

The two joint SG+ML controls and the separate phase/memory controls are still recovered, but the five different synthetic case labels collapse to one generator provenance group.  They therefore cannot satisfy physical cross-source replication.

Reveal regression remained **IMPLEMENTATION_VALIDATED**: all five phase winners and all five ringdown winners match the frozen synthetic truth file.

## Compiler/backend v1.0.2 status

The source now records actual extension compile-time compiler identity plus compiler-driver/version probe, source/flags/Python-ABI hashes, artifact SHA-256, and a deterministic build fingerprint.

This container does not have pybind11 headers installed, so the production native build and `run_02_backend_selftest.cmd` were not executed here.  On the Workbench machine `run_install.cmd` builds `_a056_native`, writes `build/COMPILER_PROVENANCE.json`, and `run_02_backend_selftest.cmd` writes `build/BACKEND_SELFTEST.json`.

The oneAPI/SYCL DD32 worker is also not executable in this container.  `run_35_sycl_worker_smoke.cmd` is intended for the Arc A770/oneAPI environment.  It builds a content-addressed worker with `-fp-model=precise` and evaluates the DD32-vs-FP32 arithmetic smoke.  DD32 is not treated as IEEE FP64 or confirmatory scientific evidence.

## Framework-v1.0.3 Gate-5 patch validation

The separately shipped Gate-5 patch was checked with `git apply --check` against the recovered v1.0.2 baseline and its dedicated regression suite passed **3/3** tests: same-generator synthetic labels do not become cross-source replication, two physical groups do pass, and same-solver simulation seeds remain non-physical replication.

## Real-data status

No real PKLSA/Euler/finite-core dynamic provider was supplied to this validation.  Therefore v0.2.1 makes **no SST physics claim**.
