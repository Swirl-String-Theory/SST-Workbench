# Axial vortex-bundle mode analysis

Rows analyzed: **4090**.
Summary files used: **14**; skipped as incompatible: **5**.

## Mode separation

- Physical-tube rows: 1038
- Numerical-discretization rows: 1946
- Continuum-reference rows: 1106

Physical tubes hold circulation per tube fixed, so total circulation grows as `N * Gamma_tube`.
Numerical discretization holds total bundle circulation fixed, so each tube carries `Gamma_total / N`.

## Backreaction gate

Full three-dimensional bending and mutual evolution of the axial tubes is **not certified in v0.3.1**. All bundle results use frozen infinite straight tubes.

## Numerical convergence by tube count

| N | matched | mean velocity-field error | mean intrinsic-residual error | clock-rate error |
|---:|---:|---:|---:|---:|
| 1 | 368 | 0 | 4.43932e-17 | 0 |
| 7 | 368 | 0.000194257 | 0.000725305 | 0 |
| 19 | 368 | 0.000239146 | 0.000625075 | 0 |
| 37 | 368 | 0.00014212 | 0.000370309 | 0 |
| 61 | 366 | 0.000111027 | 0.000288529 | 0 |
| 91 | 108 | 7.43648e-05 | 0.000319348 | 0 |
