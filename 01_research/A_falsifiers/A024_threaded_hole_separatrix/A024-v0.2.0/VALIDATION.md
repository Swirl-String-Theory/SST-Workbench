# Validation — SST Threaded-Hole Substrate Blind Falsifier v0.2.0

Validation was performed on the packaged source tree before final ZIP creation.

## Python regression suite

```text
19 passed
```

Coverage includes:

- anonymous prepare hides carrier and condition identity;
- source/geometry generation and triple-link topology checks;
- finite velocity and pressure-Poisson smoke tests;
- Windows UTF-8 text I/O regression;
- free `1/r^nu` exponent recovery on synthetic `nu=1` and `nu=2` profiles;
- carrier-cluster inference does not count repeated beta settings as independent carriers;
- pressure-law `A beta + B beta^2` recovery and even/odd decomposition;
- hierarchical contact gate prevents truncated AUC/RPO/Floquet scoring;
- best-small-rational phase-lock discovery;
- exact finite segment crossing detection;
- anonymous A-B induced-profile exponent is invariant to pair orientation and its coefficient flips sign;
- SHA-256 seal verification rejects post-seal result tampering.

## C++17 / OpenMP

`cpp/native.cpp` passed a real C++17/OpenMP syntax compile against pybind11 headers.

A temporary Linux extension was compiled and dynamically loaded. Native smoke results:

```text
backend: cpp-pybind11
32-point ring vortex_velocity: finite
exact nonlocal segment gap: finite
```

No Linux `.so` binary is included in the final artifact. Windows builds use `setup_native.py` with MSVC `/std:c++17 /O2 /openmp` and retain the `py::ssize_t` portability fix validated previously on MSVC/Python 3.14.

## v0.2 extended preregistration prepare

Standard `preset_extended.json` preparation produced:

```text
campaign format: SST-THREADED-HOLE-BLIND-2
qualified carriers: 8
blind pairs: 32
anonymous candidates: 40
strict initial clearance: d_min/a > 2.5
```

The standard threaded construction excluded only:

```text
TWIST_6_1: combined initial gap/core ~= 2.113 < 2.5
```

The other standard carriers passed. In particular, the v0.2 separated far-return sectors removed the artificial near-contact introduced when every substrate loop used the same far-return direction.

## Additional prepare campaigns

Successful preparation counts:

```text
pressure_law:       96 pairs / 104 candidates
far_field:          12 pairs / 18 candidates
similarity:         12 pairs / 24 candidates
triple_gear:        36 pairs / 45 candidates
stability_islands: 336 pairs / 378 candidates
```

The stability-island campaign generated 42 qualified geometry combinations before beta expansion.

## End-to-end native blind/seal/reveal smoke

A one-pair native far-field campaign was executed through:

```text
prepare -> blind -> SHA-256 seal -> reveal
```

Observed blind state:

```text
backend: cpp-pybind11
winner: UNSCORED
basis: NO_BLIND_PAIR_SCORE
condition identity read: false
carrier identity read: false
gravity target used: false
anonymous induced-profile nu was already present in blind_pair_results.csv
```

For that smoke case the anonymous A-B profile produced:

```text
nu_best = 3.0
R^2 ~= 0.9483
multi-grid/box nu span = 1.1
```

Reveal verified the seal and correctly returned an indeterminate free-exponent result plus failed/insufficient far-field convergence. This is a useful negative smoke result: the new gate does not force a Newton-like exponent.

## Triple-gear phase smoke

A native one-pair `TRIPLE_GEAR_T3_3` run reached the full horizon for both anonymous candidates. The geometric phase-lock analyzer returned finite phase rates, a finite phase-lock score, and a discovered low-order rational relation. No mechanical gear ratio was supplied to the blind analysis.

## Interpretation

Validation establishes software integrity and the intended blind methodology. It does not establish SST physics. The pressure, self-confinement, free-exponent, convergence and phase-lock gates remain independently falsifiable campaign outputs.
