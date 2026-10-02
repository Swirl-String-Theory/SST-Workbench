# Validation — SST Threaded-Hole Substrate Blind Falsifier v0.2.1

Validation was performed on the reconstructed v0.2.1 source tree before final packaging.

## Python regression suite

```text
24 passed
```

New v0.2.1 regressions explicitly cover:

- zero-circulation ghost threads excluded from physical contact;
- zero-circulation ghost threads excluded from Kelvin/CFL restriction;
- free-space Green kernel reproduces exact `1/r` scaling for a point source;
- geometric central-helix phase responds correctly to a rigid azimuthal phase change;
- the fixed confirmatory preregistration expands to exactly four blind pairs.

The prior v0.2.0 blind/seal, carrier clustering, pressure-law, hierarchical contact, Windows UTF-8, topology and tamper regressions remain in the suite.

## Presets

All 13 JSON presets parse successfully.

Native-accelerated preregistration preparation produced:

```text
extended:                  32 pairs / 40 candidates
pressure_law:              96 pairs / 104 candidates
far_field:                 12 pairs / 18 candidates
similarity:                12 pairs / 24 candidates
confirmatory_stability:     4 pairs / 6 candidates
thread_focusing:           24 pairs / 36 candidates
triple_gear:               36 pairs / 45 candidates
fixed_per_thread:          50 pairs / 75 candidates
stability_islands:        588 pairs / 630 candidates
```

The large stability count follows 7 qualified carriers × 2 thread counts × 3 helix settings × 14 nonzero beta values.

## C++17 / OpenMP

`cpp/native.cpp` passed a real `g++ -std=c++17 -fopenmp -fsyntax-only` compile against Python 3.13 and pybind11 headers. No unqualified POSIX `ssize_t` regression is present.

A temporary Linux pybind11 extension was compiled and loaded:

```text
backend: cpp-pybind11
```

The temporary `.so` is removed before packaging. Windows continues to build the unchanged native kernel with MSVC `/std:c++17 /O2 /openmp`; the previous `py::ssize_t` portability fix remains intact.

## Native free-space blind/seal/reveal smoke

A one-pair `TORUS_T2_3` pressure-only campaign ran through:

```text
prepare -> blind -> SHA-256 seal -> reveal
```

Blind certification:

```text
backend: cpp-pybind11
carrier identity read: false
condition identity read: false
gravity target used: false
valid pairs: 1/1
```

The smoke induced source monopole had the correct sign after reveal, while the freely fitted exponent was about `nu=3.75`; the gravity closure therefore remained unsupported. This is a useful negative validation: the new free-space gate does not force `nu=1`.

## Triple-gear phase smoke

A short native `T(3,3)` run reached the full horizon for both anonymous candidates. The v0.2.1 marker-invariant phase analyzer returned finite, nonzero thread and carrier phase rates. One anonymous condition produced a low-order rational fit near `4:1`; the other did not. This is diagnostic validation only, not evidence for a physical gear ratio.

## Gravity methodology

The primary gravity path now:

1. samples the full pressure source without mean subtraction;
2. integrates it with the open-space Green function;
3. measures source monopole/dipole/quadrupole moments;
4. seals the anonymous active/null difference exponent and monopole before reveal;
5. requires both exponent and monopole convergence across the box/grid ladder.

The enlarged source boxes contain the complete remote return legs of the closed thread loops.

## Interpretation

Validation establishes software integrity and intended falsifier behavior. It does not establish SST physics. Stability, thread focusing, pressure deficit, source monopole, asymptotic exponent, convergence and phase locking remain independent falsifiable outputs.
