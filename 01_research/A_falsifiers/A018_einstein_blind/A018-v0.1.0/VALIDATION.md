# Validation status — v0.1.0

## Completed in the build environment

- Python syntax compilation: **PASS**.
- Complete QUICK reference-backend campaign: **completed with no ERROR**.
- Blind manifest generation and forbidden-target audit: **PASS**.
- Automatic gate ordering E3 → E4 → E5 → E2 → E1: **PASS**.
- Result serialization: **PASS**.
- Result ZIP routine: **PASS** by code-path inspection; production run creates it automatically.

The physics gate verdicts from development validation are intentionally not recorded here, to avoid turning an implementation smoke test into an expected-result key.

## Native validation limitation in this environment

The current build container has a C++ compiler but does not contain the `pybind11` Python package/headers, so the native extension was **not compiled here**. `run_native_selfcheck.py` is included and mandatory in every `RUN_ALL*.cmd` research route. It compares C++ and NumPy outputs for:

- regularized Biot–Savart velocity;
- filament energy;
- hydrodynamic impulse;
- discrete curvature;
- one RK4 step.

Tolerance: relative error `2e-11` for each test.

On Windows the build first attempts C++17 + OpenMP and automatically retries C++17 without OpenMP if the OpenMP compile/link step fails.
