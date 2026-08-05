# Axial vortex-bundle mode analysis

Rows analyzed: **18**.

## Mode separation

- Physical-tube rows: 6
- Numerical-discretization rows: 10
- Continuum-reference rows: 2

Physical tubes hold circulation per tube fixed, so total circulation grows as `N * Gamma_tube`.
Numerical discretization holds total bundle circulation fixed, so each tube carries `Gamma_total / N`.

## Backreaction gate

Full three-dimensional bending and mutual evolution of the axial tubes is **not certified in v0.3.0**. All bundle results use frozen infinite straight tubes.

## Numerical convergence by tube count

| N | matched | mean velocity-field error | mean intrinsic-residual error | clock-rate error |
|---:|---:|---:|---:|---:|
| 1 | 2 | 0 | 1.74916e-16 | 0 |
| 7 | 2 | 0.000334538 | 0.000923358 | 0 |
| 19 | 2 | 0.000368398 | 0.00115875 | 0 |
| 37 | 2 | 0.000222937 | 0.000708331 | 0 |
| 61 | 2 | 0.000176325 | 0.000563111 | 0 |
