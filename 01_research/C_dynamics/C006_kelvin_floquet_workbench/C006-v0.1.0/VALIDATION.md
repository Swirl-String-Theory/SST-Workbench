# Validation — v0.1.0

Validation was performed on 2026-08-10 in the artifact build environment.

## Unit tests

```text
6 passed in 0.75 s
```

Coverage includes:

- Kelvin long-wave formula consistency;
- regularized Biot–Savart Python behavior;
- non-trivial resonance enumeration rules;
- target-blind source checks.

## Python fallback quick campaign

The complete four-phase `quick` protocol was executed with `--force-python` in 32.21 s. The archived outputs are under `reference_fallback_quick/`.

```text
K0   PASS
K1   PASS
K2   SKIP        native parity cannot be tested in force-Python mode
K3   PASS
K4   PASS
K5   PASS
K6   SKIP        no accepted RPO; true Floquet gate remains closed
K7   PASS
K8   DIAGNOSTIC
K9   DIAGNOSTIC
K10  DIAGNOSTIC
K11  DIAGNOSTIC
K12  PASS
K13  DIAGNOSTIC
K14  PASS
```

Selected checks:

```text
K0 small-x max relative asymptotic error  = 7.1610e-2
K0 ka0=6 high-k relative error            = 2.9300e-4
K0 maximum full-dispersion root residual  = 4.6860e-12

K4 N=192 -> N=256 median frequency change = 4.1921e-2
K4 ds/eps coarse                          = 0.65450
K4 ds/eps fine                            = 0.49087

K6 best recurrence RMS / D                = 0.13289
K6 endpoint vector-field error            = 0.20533
K6 verdict                                = NO_RPO__TRUE_FLOQUET_SCIENTIFICALLY_LOCKED

K7 best nontrivial 4-wave rel. detuning   = 4.2874e-3
K7 best nontrivial 6-wave rel. detuning   = 1.8518e-3

K9 P6 selected numerical sextet            = 0.98582
K9 P6 comparison sextet                    = 0.57739
K9 P4 best 4-wave candidate                = 0.98576

K14 explicit numerical target hits         = none
```

K8/K9 are deliberately `DIAGNOSTIC`: high finite-time coherence in a seeded deterministic simulation is not promoted to a statistically established universal six-wave interaction law. K10/K11 are likewise finite-time transfer diagnostics, not stationary turbulence claims. K13 reports symmetry differences without imposing a post-hoc physical chirality interpretation.

## Native C++ validation status

The artifact sandbox did not contain the `pybind11` Python package and had no network access, so the native extension could not be compiled in this environment. Consequently K2 is correctly `SKIP`, not falsely reported as C++/Python parity.

On Windows, `run_all.cmd` is stricter than this fallback validation:

1. creates/repairs `.venv`;
2. installs `pybind11` and the other requirements;
3. compiles `cpp/native.cpp` with C++17;
4. runs `run_native_preflight.py`, which exits nonzero unless the loaded backend is `cpp`;
5. only then runs tests and K0–K14.

Thus a normal `run_all.cmd` cannot silently substitute the Python fallback for a failed native build.
