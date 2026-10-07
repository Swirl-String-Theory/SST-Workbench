# Changelog

## v0.2.1 — 2026-10-07

Framework integration release targeting the in-development **SST Falsifier Framework v1.0.2**.

- Updates the vendored framework snapshot from `1.0.0.dev0` to `1.0.2.dev0`.
- Adds `.sst_framework_root` exact-version root discovery; removes dependence on fixed parent depth.
- Retains the v0.2.0 output-path hotfix: all stages share `default_output_dir(ROOT)` and therefore use `A056-v0.2.1-outputs`.
- Adds actual native compiler/build provenance:
  - compile-time compiler identity from `_a056_native.build_info()`;
  - resolved compiler-driver/version probe when available;
  - source, flags, Python ABI and artifact SHA-256;
  - deterministic `SST-BUILD-FINGERPRINT-2`.
- Adds `run_02_backend_selftest.cmd` and `build/BACKEND_SELFTEST.json`.
- Adds a framework-level softened Biot--Savart reference/native parity kernel for backend validation.
- Upgrades the external SYCL worker to a content-addressed executable keyed by source, flags and compiler fingerprint.
- Adds experimental DD32/FP32x2 arithmetic smoke with compensated `TwoSum`/FMA residual arithmetic and `-fp-model=precise`.
- DD32 remains screening-only and is explicitly not IEEE FP64.
- Adds mandatory `evidence_class` provider metadata.
- Backports the planned framework-v1.0.3 Gate-5 fix:
  - synthetic controls grouped by generator identity;
  - simulations grouped by solver-independence identity;
  - only `independent_source` and `experimental` count toward physical cross-source replication;
  - adds `G5_CONTROL_REPLICATION` separately from `G5_CROSS_SOURCE_REPLICATION`;
  - prevents `G6_MECHANISM_PHYSICS` PASS from synthetic controls.
- Synthetic framework smoke now concludes `JOINT_CONTROL_RECOVERED`, not `JOINT_SUPPORTED`.
- Adds `science_contract.json`, DD32 framework note, and expanded regression tests.

Scientific SG/ML equations, discovery/holdout fractions, BIC thresholds, alpha support interval, and numerical convergence thresholds are unchanged from v0.2.0.
