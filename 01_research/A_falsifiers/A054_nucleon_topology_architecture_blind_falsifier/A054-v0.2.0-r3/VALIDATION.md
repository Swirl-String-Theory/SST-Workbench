# Validation — A054 v0.2.0

Validation performed in the ChatGPT Linux execution environment on 2026-10-06.

## Static/unit validation

```text
19 passed, 1 skipped
```

The skipped test is the native C++/pybind11 parity test because a compatible built extension is not present in this Linux environment. The package keeps an independent NumPy reference backend. On Windows, `run_00_install.cmd` attempts the C++17/OpenMP build and EXTENDED/FULL require the native OpenMP backend fail-closed.

Covered tests include:

- v0.1.1 blindness, geometry and packaging regression tests;
- PKLSA discovery/factorial preparation;
- v0.2.0 mode-basis orthogonality and family presence;
- BASIC cohort cardinality (28 anonymous cells with mocked upstream providers);
- separation-Hessian symmetry/finite values;
- `no accepted RPO -> Floquet not evaluated`.

## End-to-end smoke

A low-cost analytic three-component link smoke run exercised:

```text
projected Jacobian -> epsilon convergence -> restoring probe ->
Kelvin/full spectrum -> nonlinear ringdown -> RPO search -> conditional Floquet
```

It completed without exception on the NumPy reference backend. The intentionally short smoke trajectory did not certify the test geometry and found no RPO; accordingly the Floquet output was exactly:

```text
NOT_EVALUATED_NO_RPO
```

This is the required fail-closed behavior, not a failed Floquet multiplier test.

## Scientific boundary

Validation establishes software-path integrity only. It does not establish nucleon stability. A scientific result requires the preregistered BASIC/EXTENDED/FULL campaign against the E010/E011 PKLSA provider envelope, followed by blind review before reveal.


## r2 execution validation

- Source suite on Linux container: `19 passed, 1 skipped` (native extension unavailable in container).
- Negative fail-closed builder check: `--require-openmp` exits non-zero when no native extension exists.
- Windows acceptance condition: source backend must qualify `cpp_pybind11_openmp`; temporary isolated-runner preflight must then import `a054_blind._native` with `openmp_enabled=true` before `prepare-cert`.
- Scientific configs and thresholds are unchanged from v0.2.0.
