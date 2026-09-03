# Validation — v0.2.2

Generation-time validation was executed against the final strict-blind source tree.

## Static blind constant/SI leakage guard

Result: **PASS**.

The guard scanned the complete pre-reveal scientific path and found zero forbidden
canonical SST numerical fingerprints, zero reveal/provenance imports, and zero
forbidden canonical symbols.

See `validation_reference/BLIND_CODE_AUDIT.json`.

## Python unit tests

```text
8 tests run
7 PASS
1 SKIP
```

The skipped test is native C++/Python parity because the generation environment does
not have the compiled extension loaded. No native PASS is claimed here.

See `validation_reference/unittest.txt`.

## Synthetic dimensionless universal-action positive control

Blind verdict:

```text
PASS = True
median Jf_hat = 0.371956194259
CV = 0.00396932
median amplitude log-slope = -0.000453577
```

The control uses an arbitrary dimensionless action constant and no Planck/SST target.

## Synthetic classical-continuity negative control

Blind verdict:

```text
PASS = False
classical continuity null triggered = True
median amplitude log-slope = 1.99943
```

This intentionally reproduces approximately quadratic classical energy scaling and
is rejected by UA4/UA5/UA6.

## Raw-geometry fallback smoke test

The bundled demo geometry was evolved with the pure-Python backend, dimensionless
normalization and the fallback validation preset.

Blind verdict:

```text
PASS = False
UA0 no SST/SI target leak = True
positive resolved dimensionless energy = False
```

The run failed closed on unresolved/negative dimensionless energy increments rather
than manufacturing an action value from numerical clipping.

## Native scientific campaign status

A production Windows run must still demonstrate:

- MSVC build success;
- native backend actually loaded;
- native/Python Biot–Savart parity;
- native/Python energy parity;
- RK4 evolution parity;
- temporal and spatial convergence on the real dataset.

No physical SST/Planck result is included in this validation.


## v0.2.2 Windows-build hotfix validation

The supplied user log establishes that v0.2.1 successfully created the Python 3.14 venv and installed NumPy/pybind11, then failed before compiling `native.cpp` while setuptools invoked its own `cmd /u /c vcvarsall.bat ... && set` bootstrap.

This release changes only Windows environment/bootstrap runners. Static package checks and Python unit tests were rerun in the generation environment. A real MSVC PASS remains intentionally unclaimed until the user's Windows machine executes `run_01_build_native_clean.cmd` and the native/Python parity self-test passes.
