# SST Horn Dirichlet Gate Harness

Self-contained audit harness for the SST hollow-core horn-torus Dirichlet subproblem.

This package separates the kinetic Dirichlet factor from cavitation work:

\[
\chi_K(\lambda)=\frac12\int_{\tilde\Omega_\lambda}|\tilde{\mathbf v}|^2\,d^3\xi,
\qquad
\chi_{\rm cav}(\lambda)=\pi^2\lambda,
\qquad
\chi_E^{\rm hollow}=\chi_K+\chi_{\rm cav}.
\]

Status: **research-track audit harness**. The included C++ backend is a first-pass regularized circular-ring field candidate, not a final boundary-element solution of the harmonic Neumann-period problem. It is intentionally useful because it runs all gates and can fail them explicitly.

## Install prerequisites

Python dependencies:

```bash
python -m pip install numpy pybind11
```

A C++17 compiler is required for the pybind11 extension. If pybind11 is absent, the package falls back to a slower NumPy backend so the audit interface still works.

## Run

From this folder:

```bash
python run_horn_gates.py --lambda 1.2 --n-ring 256 --n-surface 48 --n-volume 26 --box-radius 6.0
```

Run a sweep and write CSV/JSON:

```bash
python run_horn_gates.py --sweep 1.05 1.1 1.2 1.5 2.0 --out results-sweep
```

## Files

- `run_horn_gates.py`: command-line runner.
- `sst_horn/build_ext_if_needed.py`: hash-based build script. Rebuilds only when C++ source or build metadata changes.
- `sst_horn/horn_gates.py`: Python API, gates, JSON/CSV output.
- `sst_horn/_fallback.py`: pure NumPy fallback backend.
- `cpp/hornkernels.cpp`: pybind11 C++ heavy backend.

## Gate semantics

The output reports:

- `chi_K`: kinetic-only Dirichlet factor, estimated on a finite box.
- `chi_cav = pi^2 lambda`.
- `chi_E_hollow = chi_K + chi_cav`.
- `residual_kinetic_to_2pi`.
- `residual_total_to_2pi`.
- `circulation_error`.
- `neumann_boundary_error`.
- `divergence_error`, `curl_error` by finite differences.
- `farfield_decay_error`.
- `gate_*_pass`: boolean pass/fail flags using conservative default thresholds.
- `solver_kind`: `pybind11_regularized_ring` or `numpy_fallback_regularized_ring`.

The mathematically decisive analytic guard is also included: with positive cavitation work,

\[
\chi_E^{\rm hollow,horn}=\chi_K^{\rm horn}+\pi^2>2\pi.
\]

So a total-energy hollow horn-torus cannot match \(2\pi\) without excluding cavitation work, adding a negative renormalization term, changing geometry, or replacing the hollow-core ansatz with a resolved-core model.


## Windows / MinGW build note

If the direct pybind11 command is compiled with MinGW/Strawberry and fails with many
`undefined reference to __imp_Py...` linker errors, the build script now adds the
CPython import-library link flags automatically on Windows and then tries a
`setuptools build_ext --inplace` fallback.  If no compatible compiler/Python import
library is available, the package continues with the NumPy backend.

Manual checks:

```bash
python -m sst_horn.build_ext_if_needed --force
python run_horn_gates.py --lambda 1.2 --n-ring 256 --n-surface 48 --n-volume 26 --box-radius 6.0  --out results
python run_horn_gates.py --lambda 1.2 --no-cpp
```

Use strict mode only when you want CI to fail if the C++ extension is unavailable:

```bash
python -m sst_horn.build_ext_if_needed --force --strict
```