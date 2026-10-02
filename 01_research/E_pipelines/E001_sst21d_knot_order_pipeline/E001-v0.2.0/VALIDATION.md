# Validation report — SST-21D Knot Order Pipeline v0.2.0

## Environment

```text
Python package import: PASS
C++17 CMake build: PASS
Native shared-library loading: PASS
pytest: 11 passed
```

The platform-specific native build directory is not required in the release archive; Windows users rebuild it using `RUN_BUILD_NATIVE.bat` or either `RUN_FRESNEL_ALL*.cmd` script.

## Input-format validation

Bundled `data/Fresnel_FourierSeries.zip`:

```text
78 .fseries
76 .short
73 paired stems
5 Fourier-only
3 short-only
0 parse errors
```

Both three-decimal and six-decimal zero spellings are covered by regression tests. The parser also accepts signed zero and Fortran `D` exponents.

## Harmonic-origin validation

All 78 Fourier files received an explicit harmonic origin:

```text
harmonic_origin = 0 : 42
harmonic_origin = 1 : 36
unresolved            : 0
```

For paired files the rejected candidate was at least 10.02 times worse in normalized closed-curve RMSD than the selected candidate. No paired decision was low-confidence.

## Full static campaign

Command:

```text
python -m sst21d fresnel-static
  --input data/Fresnel_FourierSeries.zip
  --samples 600
  --prefer short
  --metadata data/sst21_metadata_seed.csv
  --origin-overrides data/fseries_origin_overrides.csv
  --out outputs/fresnel_static
  --require-native
```

Result:

```text
81 master rows
154 representation rows
76 rows selected from .short
5 rows selected from .fseries fallback
81/81 selected rows used the native C++ backend
73/73 paired representations passed normalized shape RMSD <= 0.10
```

Pair shape agreement at 600 samples:

```text
minimum RMSD : 0.00617
median RMSD  : 0.03458
maximum RMSD : 0.07773
```

## Convergence smoke campaign

Fourier representations were tested at 128, 256, and 512 points:

```text
47/78 passed all default diagnostic thresholds
31/78 require higher resolution or metric-specific review
```

This is not treated as a package failure. In particular, midpoint writhe and sampled reach can converge more slowly than polygonal length. `RUN_FRESNEL_ALL_MAX.cmd` extends both representation campaigns through 1024 points.

## Export round trip

Eleven representative variants were exported as TXT and VECT at 240 points. All were read back successfully with one closed component and exactly 240 vertices.

## Claim guard

The successful tests establish parser behavior, representation agreement, reproducible geometry diagnostics, and native/Python execution. They do not establish:

- an independently certified knot polynomial;
- exact ropelength or thickness;
- Ridgerunner constrained residual convergence;
- phase order or Goldstone dispersion;
- physical particle identity in SST.
