# A054 v0.2.0-r2 — isolated native-runner hotfix

Scientific configuration is unchanged from v0.2.0 / r1.

## Fixed

The r1 source environment correctly qualified CPython 3.14 + `cpp_pybind11_openmp`, but
`build_blind_runner.py` could silently continue if the native extension failed to import after
copying into the isolated `a054_blind` package. FULL then failed later with `numpy_reference`.

r2:

1. imports the native extension with the exact venv interpreter and copies that exact file;
2. renames the isolated copy deterministically to `_native.pyd` on Windows (`_native.so` elsewhere);
3. probes `a054_blind._native` in a clean child process after the copy;
4. requires `openmp_enabled == true` for EXTENDED/FULL;
5. fails immediately in `build_blind_runner.py` if isolated native qualification fails;
6. pre-imports the same native extension again in `run_cert.py` before loading the certification stack;
7. records source path, isolated path, probe path, and OpenMP status in `RUNNER_MANIFEST.json`.

No candidate geometry, threshold, perturbation, mode basis, RPO rule, or reveal logic was changed.

## Early preflight

`run_all_extended.cmd` and `run_all_full.cmd` now build and import a temporary isolated blind
runner before `prepare-cert`. A failed sandbox/OpenMP import therefore stops before the expensive
candidate preparation step.

## Default workbench root

`run_all.cmd`, `run_all_extended.cmd`, `run_all_full.cmd`, and `run_02_prepare_cert.cmd` no longer
require a mandatory first positional argument. Resolution order:

1. CLI argument `%1` when provided
2. environment variable `SST_WORKBENCH_ROOT`
3. default `C:\workspace\projects\SST-Workbench`

Missing roots fail closed with a clear error before install/prepare.
