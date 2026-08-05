# Validation record for v0.2.1

The release source was validated with a locally compiled Linux CPython 3.13 C++17/pybind11
extension. Platform-specific `.so`/`.pyd` binaries are intentionally excluded from the release ZIP;
the active interpreter rebuilds the extension from `cpp/native.cpp`.

## Automated tests

```text
12 passed in 4.25 s
```

The tests cover:

- all 18 requested IDs and the complete 130-link source count;
- Fourier periodicity through the third derivative;
- exact Hopf-link component lengths, linking number and diameter contact;
- rigid, mirror and orientation invariances;
- backend-option contract checks;
- native/Python parity for two- and three-component links;
- iterative union-find on chains longer than Python's recursion limit;
- `L2a1` continuous-contact handling without recursion overflow;
- local Fourier curvature refinement;
- Ridgerunner OOGL VECT export/read round trip.

## Native parity

Strict native parity passed for `L2a1` and `L6a4` at

```text
epsilon/D = 0.05, 0.10, 0.20.
```

Representative maximum differences were at floating-point scale:

```text
velocity absolute error:       <= 2.220446049250313e-16
Gauss-linking absolute error:  <= 4.440892098500626e-16
Neumann absolute error:        <= 4.440892098500626e-16
```

The full machine-readable record is `validation/native_parity.json`.

## Campaign validation

- Smoke set `L2a1`, `L6a4`, `L7n2`: 3/3 completed, zero failures.
- Quick requested set: 18/18 completed, zero failures.
- Full requested set: 18/18 per-link ledgers and combined report, zero failures.
- Full `L2a1` regression: completed at `N=1024`; recursion failure removed.
- Ridgerunner bridge smoke: `L2a1` and `L6a4` exported and round-tripped.

The packaged Windows launcher deliberately runs one link per Python process and rebuilds the final
catalogue from the resulting ledgers. This is a robustness policy for long OpenMP/native campaigns,
not a change to the mathematical kernels.

## Scope of validation

A complete 130-link v0.2.1 production campaign was **not** preregistered as a release-validation
claim. The package supports it through `-AllDatabase`; the included evidence establishes the native
kernels, the corrected `L2a1` path and the complete requested 18-link gate set.

Ridgerunner itself is external and was not invoked during release validation. Only the VECT bridge,
normalization metadata and round-trip parser were tested.
