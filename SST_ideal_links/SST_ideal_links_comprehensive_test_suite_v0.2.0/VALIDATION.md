# Validation record for v0.2.0

The release source was validated before packaging with a locally compiled Linux CPython 3.13 extension. The platform-specific `.so` is intentionally excluded from the release ZIP; the package rebuilds locally from `cpp/native.cpp`.

## Automated tests

```text
8 passed
```

Coverage includes:

- all 18 requested IDs and the 130-link database count;
- Fourier periodicity through the third derivative;
- exact Hopf-link component lengths, contact distance and linking number;
- rigid, mirror and orientation invariance;
- mutually exclusive backend flags;
- native/Python parity for two- and three-component links.

## Strict-native campaign validation

- Smoke set: `L2a1`, `L6a4`, `L7n2` — 3/3 completed.
- Full preregistered quick set — 18/18 completed.
- Native parity gate — passed.
- Campaign failures — zero.

## Native benchmark

Representative case:

```text
link: L6a4
components: 3
samples per component: 192
circulation sectors: 8
epsilon/D: 0.1
```

Measured on the validation container:

```text
C++ best:    0.002768616 s
NumPy best:  0.057902613 s
speedup:     20.9139x
max error:   2.220446049250313e-16
relative L2: 1.50621650914607e-16
```

This benchmark is hardware- and compiler-dependent; the parity error is the primary correctness result.
