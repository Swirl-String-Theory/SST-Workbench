# Fresnel `.fseries` / `.short` format audit

## Archive inventory

The bundled archive contains:

```text
157 total stored files
78 .fseries files
76 .short files
73 exact same-stem pairs
5 .fseries-only variants
3 .short-only variants
0 parser failures
```

Fourier-only variants:

```text
1_1/knot.1_1
9_2/knot.9_2
9_2/knot.9_2n
10_1/knot.10_1
10_1/knot.10_1n
```

Polygon-only variants:

```text
4_1/knot.4_1i8
8_3/knot.8_3i8
8_9/knot.8_9i4
```

## The `000` versus `000000` observation

The files use several textual zero styles, including:

```text
0
0.0
0.000
0.000000
-0.000000
```

These are lexically different but numerically identical. The parser therefore:

1. converts all valid decimal and Fortran `D`-exponent tokens to finite `float64` values;
2. records the original zero spellings in `*_zero_token_styles`;
3. never infers Fourier indexing from decimal width.

`.short` files contain exactly three fields per numeric row:

```text
x y z
```

`.fseries` files contain exactly six fields per numeric row:

```text
a_x b_x a_y b_y a_z b_z
```

## Actual ambiguity: implicit harmonic index

The row number is not stored explicitly. Two conventions occur:

```text
j = 0,1,...,M-1
j = 1,2,...,M
```

An all-zero first row does not prove `j=0`, because symmetry may force the true first harmonic to vanish.

For the 73 paired files the package reconstructs both candidate curves and compares each with the `.short` polygon after removing translation, scale, proper rotation, cyclic parameter shift, and parameter reversal.

Results:

```text
42 Fourier files resolved as harmonic_origin = 0
36 Fourier files resolved as harmonic_origin = 1
78/78 Fourier files resolved
73 resolved by paired .short Procrustes comparison
2 resolved by an explicit "constant term set to 0" comment
3 resolved by a nonzero first row and no explicit constant row
```

For the 73 paired decisions:

```text
accepted normalized RMSD: min 0.00858, median 0.03498, max 0.07689
rejected/accepted RMSD ratio: min 10.02, median 29.70, max 128.81
```

Thus the two index conventions are cleanly separated in this archive.

## Representation agreement

At 600-point common arclength sampling, all 73 `.fseries`/`.short` pairs pass the preregistered normalized shape threshold

\[
\epsilon_{\rm pair}\le 0.10.
\]

The raw scale is not generally equal: `.short` geometries are frequently scaled relative to the Fourier coefficients. Therefore shape RMSD is scale-normalized, while length and RMS-radius ratios are reported separately.

## Remaining scientific limitation

Representation agreement verifies that two files encode the same geometric shape up to the stated transformations. It does not independently certify the knot type, thickness, ropelength minimum, or dynamical SST stability.
