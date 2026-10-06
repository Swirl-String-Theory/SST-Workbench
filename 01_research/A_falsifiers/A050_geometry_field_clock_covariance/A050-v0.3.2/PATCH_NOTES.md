# A050 v0.3.2 patch notes

## Basis

This package is built directly from the clean A050 v0.3.0 source state. It intentionally does not depend on the earlier v0.3.1 overlay/hotfix.

The supplied frozen v0.3.0 output is used only as declared post-hoc motivation. Its `blind_results.json` SHA-256 is:

`45039df0f5d30e10c01dfdee5f2a1071ff5a7e1f11c12245bd1956915a4ed4a7`

The parent verdict remains `REAL_GEOMETRY_MODAL_TRANSFER_NOT_REPRODUCED`.

## Scientific change

v0.3.2 separates two questions that v0.3.0 coupled:

1. Does the dynamically selected branch label survive the baseline/holdout perturbation panel?
2. If it survives, is its phase stationary, coherently drifting, coherently reversing, complex-but-locally-coherent, or unresolved?

No numerical mode is hard-coded. Branch retention is no longer conditioned on the old stationary `persistence.pass` flag.

## New diagnostic classes

- `STATIONARY_COHERENT`
- `COHERENT_DRIFTING`
- `COHERENT_REVERSING`
- `COHERENT_NONSTATIONARY_COMPLEX`
- `INCOHERENT_OR_UNRESOLVED`

Angular rate is explicitly `omega = d(phi)/dt` in radians per dimensionless time; `f = omega/(2*pi)` is the corresponding cycle rate.

## Installation

Recommended: run `make_A050_v0.3.2_from_v0.3.0.cmd` with the v0.3.0 directory as its first argument, or run it while your current directory is A050-v0.3.0.

The script creates a sibling `A050-v0.3.2`, excludes `.venv`, caches, staged data, previous outputs, and any old `overlay` directory, then applies the v0.3.2 overlay. It does not modify A050-v0.3.0.

After installation:

```bat
cd /d C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A050_geometry_field_clock_covariance\A050-v0.3.2
run_all.cmd C:\workspace\projects\SST-Workbench
```

## Validation performed while building this package

- 5/5 synthetic unit tests pass: stationary, chirp, coherent reversal, random phase rejection, branch-retention independence from parent persistence pass.
- v0.3.0 parent-output regression: 5/5 primary baselines are stable branch identities and 25/25 holdouts retain their baseline branch under the v0.3.2 branch rule, while the parent persistence flags remain unchanged.
- Python compile/import smoke test passes.
- Focused end-to-end filament evolution smoke test passes.
- blind-code/config audit returns zero leakage hits.
- `git apply --check` passes against the clean v0.3.0 baseline used to construct the patch.
