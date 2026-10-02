# Validation — v0.3.5

## Contract / unit tests

- 35 non-native tests passed with the native/backend-specific tests deselected.
- 3 native/backend tests passed separately.
- Combined test count: **38 passed**.
- Python compileall over `src/`, `scripts/`, and `tests/`: PASS.

## Native backend

Linux validation build: C++17 + OpenMP native preflight PASS. The release contains no compiled `.so`/`.pyd`; Windows builds its own CPython-ABI-specific extension locally.

## v0.3.5 bug regression

Raw `qm_full` on `L6a4` with configured `N=96` now aborts at `qm_spectral_preflight.json` before Biot-Savart/Hessian evaluation. The ledger reports:

- source active mode: 255;
- strict Nyquist floor: 512;
- nonlinear sampling floor: 1024;
- configured/effective N under fixed policy: 96;
- campaign result: fail-fast spectral preflight.

This closes the v0.3.4 defect where an invalid-looking full Hessian was computed and only rejected post hoc.

## Resolved working-geometry checks

For Borromean `L6a4` the preflight passes for:

- full Hessian cutoff m<=64 at N=384;
- full Hessian cutoff m<=96 at N=512;
- full Hessian cutoff m<=128 at N=768;
- raw source with explicit `auto-nonlinear`, promoted to N=1024.

A strict-native filtered quick `L6a4` smoke run completed 1/1 with zero failures.

## Claim boundary

The matched m=64/96/128 **full-Hessian cutoff ladder has not been run to completion in this packaging environment** because it is intentionally expensive. The runner and stage configs are included for local execution. Cutoff stability is a Research Track numerical-regularization result, not a physical SST cutoff derivation.
