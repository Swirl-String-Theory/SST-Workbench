# Changelog

## v0.3.0 hotfix 3 — Windows runtime-directory reset
- Repeated E010 provider runs no longer delete the `data/runtime_e010_*` directory root with `shutil.rmtree()`.
- Runtime and private-reveal roots are retained and emptied child-by-child, avoiding Windows `WinError 5` on the final `os.rmdir()` when an indexer/AV/Explorer handle is present.
- Read-only stale entries are made writable before deletion and transient sharing failures are retried with bounded backoff.
- The provider still fails closed if a stale child cannot be removed; stale data is never mixed into a new run.
- Added regression tests proving the runtime root is never passed to `shutil.rmtree` and read-only stale files are removed.
- Scientific/preregistered protocol unchanged.

## v0.3.0 hotfix 1 — Windows provider entry-point bootstrap
- Fixes `ModuleNotFoundError: No module named 'a056_provider'` when `tools\build_e010_provider.py` is executed as a file on Windows.
- The tool now explicitly inserts the A056 instance root into `sys.path` before importing instance-local packages.
- `run_e010_filament.cmd`, `run_e010_euler_smoke.cmd`, and `run_e010_euler_convergence.cmd` now invoke the provider as `python -m a056_provider.campaign`, which is the preferred package-safe entry point.
- Adds a subprocess regression test for direct-script invocation.
- No science contract, frozen protocol, thresholds, provider equations, blindness rules, or framework v1.0.4 code changed.

## v0.3.0
- First real E010/PKLSA dynamic-provider release.
- Adds strict live E010-v0.3.1 carrier admission/hash verification derived from the audited A047 route.
- Adds paired finite-core Biot-Savart filament and 3-D incompressible Euler provider lanes.
- Freezes Bishop-frame Kelvin perturbation, common rigid-motion registration, residual phase and projected mode envelope before scoring.
- Adds provider reveal commitment before model scoring.
- Adds same-carrier cross-resolution convergence and prevents resolution replay pseudo-replication.
- Simulation evidence can produce a simulation conclusion but remains ineligible for physical G7.
- Remains pinned to SST Falsifier Framework v1.0.4 CANONICAL_FROZEN without framework patches.

### v0.3.0 hotfix 2 — 2026-10-07
- Real-provider launchers no longer call framework REVEAL unconditionally.
- Added fail-closed `REVEAL_IF_ALLOWED` preflight matching the frozen v1.0.4 reveal policy.
- Added current-run reveal decision artifact and stale-reveal cleanup.
- Provider identity reveal is conditional on verified canonical framework reveal.
- Packaging cannot resurrect an older REVEALED archive after a withheld reveal.
- Scientific/preregistered protocol unchanged.

## v0.3.0 hotfix 4 - G2 diagnostic retention
- Preserve opaque per-case POD metrics when G2 terminates the blind pipeline.
- Add read-only `run_diagnose_g2.cmd` for an existing provider directory.
- No scientific gate, threshold, provider configuration, hypothesis, or reveal rule changed.
