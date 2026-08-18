# Package validation performed before delivery

The package was exercised against the three bundled relaxed sample geometries.

## Python fallback smoke

- dataset count: 3
- error count: 0
- H6 calibrations: PASS
- numerical/geometric identities: PASS
- `pipeline_ok = true`

## Native C++ parity

The C++17 extension source was compiled in the delivery environment against available pybind11 headers and CPython 3.13, then compared with the NumPy fallback.

Observed parity checks:

```text
Biot-Savart velocity relative difference ~ 1.3e-16
regularized energy relative difference  ~ 1.2e-15
planar-circle writhe absolute value      = 0
native contact kernel                    returned expected records
```

The complete BASIC and EXTENDED campaigns were then run with the native backend on all three sample files:

```text
BASIC:    error_count = 0, pipeline_ok = true
EXTENDED: error_count = 0, pipeline_ok = true
run_all:  pipeline_ok = true
```

Physical/model hypothesis FAILs occurred in the sample run, as expected for a falsifier, and were preserved rather than treated as execution errors.

The Windows `setuptools/build_ext` path is inherited from the supplied pybind template and has an added fallback that allows MSVC discovery even when no standalone `c++` executable is on PATH.
