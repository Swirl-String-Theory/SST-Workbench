# Validation — 1_Maxwell_SST_Kinetic_Falsifier v0.2.0

Validation date: 2026-08-13.

## Python tests

```text
14 passed, 1 skipped
```

The skipped test is the C++/Python numerical-parity test because `pybind11` is not installed in the artifact execution sandbox. The same test executes automatically when the native module is available on the target Workbench.

Covered by tests:

- legacy v0.1 campaign/gap/coupling/thermodynamic/taxonomy behavior;
- VECT import and closed-curve arclength resampling;
- rigid translation decomposition;
- rigid-projected Kelvin/shape candidate generation;
- Python fallback midpoint writhe on a planar circle;
- Python fallback regularized Biot–Savart finite-output check;
- conditional C++ vs Python parity for Biot–Savart, writhe and minimum distance.

## Synthetic strict-falsifier checks

Both historical synthetic datasets remain explicitly nonphysical:

```text
synthetic_pass -> DEMO_ONLY
synthetic_fail -> DEMO_ONLY
```

The failing demo continues to exercise the internal falsifier gates without permitting a synthetic dataset to acquire a physical top-level verdict.

## v0.2 solver-facing smoke workflow

Input: two synthetic closed VECT curves (`circle.vect`, `trefoil_T2_3.vect`).

Basic preset result:

```text
files_discovered      = 2
curves_parsed         = 2
parse_failures        = 0
resample_n            = 300
max_fourier_m         = 6
mode_candidates       = 48
interaction_probes    = 2
backend in sandbox    = python fallback
```

The workflow produced geometry metrics, mode-family capability declarations, rigid-projected mode candidates, interaction-coupling proxies, resampled unit-RMS curves, and a blank v0.1-compatible physical campaign skeleton.

## C++ backend status

The C++17 source and pybind build path are included and based on the supplied `SST_cpp_pybind_audit_template` pattern. Native compilation could not be executed in this sandbox because `pybind11` is not installed and outbound package installation is unavailable here.

On Windows, `run_00_install.cmd` installs `pybind11`, invokes the hash-based builder, and then `run_01_check_backend.cmd` reports whether the active backend is `cpp` or `python`. `run_20_extended.cmd` deliberately requires `cpp` to avoid silently starting the high-resolution `N=1200` campaign through the slow fallback.

## Interpretation audit

No v0.2 geometry quantity is written into the physical `gap_eV`, mode-energy-transfer, thermodynamic, or spectroscopic columns. Twist/core remain unavailable for centerline-only input. This is intentional and prevents the new accelerated layer from manufacturing physics that the current geometry data do not determine.
