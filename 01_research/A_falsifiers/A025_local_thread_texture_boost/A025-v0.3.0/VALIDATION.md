# Validation — SST Local Thread Texture + Boost Invariance Blind Falsifier v0.3.0

## Packaging-environment status

The v0.3.0 package was constructed from the user-uploaded v0.2.0 archive and then tested in the packaging environment.

### Python syntax

**PASS**

All Python modules and runners compile with `python -m compileall`.

### v0.3 selftest — Python/reference path

**PASS**

Observed synthetic-test values:

```text
exact segment vs dense quadrature relative L2  = 5.344529290872526e-11
common-boost shape RMS / Rg                    = 8.651491821773421e-16
reparameterization segment CV before           = 4.7125466279145023e-01
reparameterization segment CV after            = 1.0063849230842855e-02
finite-source field errors D/Rg=8,16,32         = 1.232331168457842e-01,
                                                   5.8807552726727365e-02,
                                                   2.907114073041607e-02
thread endpoint count                           = 0
selftest status                                 = PASS
```

The finite-source errors decrease monotonically toward the locally parallel limit.

### Mini blind campaign

**PASS**

A reduced synthetic trefoil campaign exercised:

- blind manifest generation;
- SHA-256 semantic commitment;
- opaque case execution;
- RK4 evolution;
- scoring and unblinding;
- G0--G11 report generation.

The reduced test returned:

```text
overall_structural_status          = PASS
overall_conditional_bridge_status  = PASS
```

Thresholds in that mini test were intentionally relaxed to test control flow, not scientific qualification.

### Mini spatial + temporal certification runner

**PASS**

A reduced ladder with `N=32 -> 48` plus a factor-2 temporal refinement verified:

```text
T_final relative spread = 0
fixed-core relative spread = 0
C1_spatial_fixed_core_convergence = CERTIFIED_PASS   [relaxed test thresholds]
C2_temporal_RK4_convergence       = CERTIFIED_PASS   [relaxed test thresholds]
```

This validates that the certification runner keeps `T_final` and core radii fixed while changing spatial and temporal resolution independently.

## Native C++ status in packaging environment

**NOT EXECUTED / NOT CLAIMED**

The packaging environment has `g++` but does not have the `pybind11` Python package/headers installed.  Therefore the compiled C++17 extension and native-vs-Python parity were not executed here.

This is an environment limitation, not a native PASS.

On Windows, the one-click chains perform:

```text
run_install.cmd
  -> run_build_native.cmd --strict
  -> run_selftest.cmd --require-native
  -> blind campaign/certification
```

A physical run therefore does not proceed through the standard one-click chain unless the native module builds and the C++/Python selftest passes.

## Scientific qualification

Passing execution is not equivalent to confirming SST.  In particular:

- G0--G4, G6 and G11 are structural/numerical tests;
- G5 is a finite-core admissibility diagnostic;
- G7--G10 are conditional bridge tests for the committed filament model;
- core-overlap cases are bridge-`INDETERMINATE`;
- C1 and C2 qualify spatial and temporal numerical convergence separately.
