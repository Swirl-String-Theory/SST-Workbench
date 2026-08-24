# Validation — v0.1.0

Validation date: 2026-08-21.

## Release checks

- Python regression suite: **10/10 PASS** (`pytest`).
- Python bytecode compile (`compileall`): **PASS**.
- JSON configuration parse: **6/6 PASS**.
- Native backend runtime smoke: **PASS**, backend reported `cpp-pybind11`.
- Native geometry helper smoke: **PASS**.
- Blind protocol smoke: **PASS** (`prepare -> blind -> SHA-256 seal -> reveal`).
- Blind audit fields: carrier identity unread, condition identity unread, explicit delay parameter unused, target phase unused.
- No-free-delay regression: **PASS**. Configurations contain no `tau_delay`, `phase_delay`, `feedback_delay`, `user_delay`, or target-phase parameter.
- UTF-8 text I/O: explicit `encoding="utf-8"` is used for generated reports/tables/keys.
- Release binary/cache audit: source ZIP intentionally excludes `.so`, `.pyd`, `.pyc`, `__pycache__`, `.pytest_cache`, `.venv`, build trees and outputs.

## Fresh native end-to-end smoke

A two-pair basic campaign was run with the native helper loaded. The blind stage reported:

- backend: `cpp-pybind11`;
- 2 anonymous pairs;
- 0 indeterminate pairs;
- no carrier or condition identity read;
- no explicit feedback-delay parameter;
- result tree sealed before reveal.

The post-seal reveal reported:

- finite-core mode valid fraction: `1.0`;
- median group-delay vs wave-packet-return relative error: `0.0796875`;
- self-generated delay gate: **PASS**;
- overall verdict: `MECHANISM_NOT_ESTABLISHED`.

The negative overall verdict is a desired sanity check: measuring a reproducible propagation delay does not automatically cause the mechanism verdict to pass.

## Prepared campaign sizes

| preset | blind pairs | anonymous candidates |
|---|---:|---:|
| basic | 8 | 16 |
| extended | 96 | 192 |
| profile robustness | 72 | 144 |
| core radius | 48 | 96 |
| chirality/sign | 120 | 240 |
| radial convergence | 16 | 32 |

## Scientific scope check

This release is a **slender finite-core linear incompressible-Euler mechanism falsifier**. The radial core eigenproblem is finite-core; the closed carrier supplies loop length, curvature validity and Bishop holonomy. Curvature is not yet included inside a full curved-tube 3-D Euler operator. A positive result is therefore a gate toward a curved finite-core Euler/Floquet calculation, not proof of nonlinear SST particle stability.

## Platform note

The native source targets C++17 + pybind11 + OpenMP. The release runners are written for Windows/VS2022 and build the `.pyd` locally. The Linux validation binary used during artifact testing is deliberately not shipped.
