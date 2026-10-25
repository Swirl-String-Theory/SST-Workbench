# A065 v0.3.1 qualification protocol (preregistered)

## Target-free numerical test

The original E010/KnotPlot 3_1 centerline is length 300. Subsamples are index-aligned (`[::4]`, `[::2]`, `[::1]`), and the v0.3.0 dimensionless regularized straight-midpoint-segment velocity is used throughout:

$$
\mathbf u(\mathbf x)=\frac{\Gamma}{4\pi}\sum_j
\frac{\Delta\mathbf X_j\times(\mathbf x-\mathbf X_{j+1/2})}
{(|\mathbf x-\mathbf X_{j+1/2}|^2+\epsilon^2)^{3/2}}.
$$

Only the reduced RK4 filament ODE is evolved; it is **not** a 3D Euler field solver. Fix gamma=1, eps=0.12, end time=0.04, 8 RK4 steps at every grid. Separate time-halving control on the 75-point grid uses 4 vs 8 steps. Define position difference on aligned nodes using RMS Euclidean distance, divided by the coarser grid's RMS displacement from t=0. Register `error < 0.05` for each of 75→150, 150→300 and 75→300. Every result is retained, including FAIL.

## Geometry-provider reconciliation

WorkBench E010 registration: Fremlin A006, carrier `CAR_d8a316361e0941af`, raw SHA-256 `73cd5304e79a9cf52b71c88d1d7ebc21948a6d87526b0e95ba5aa6f257150e80`. The original raw geometry is not included; different parser inputs or edited bytes cannot silently substitute. The portable run writes `outputs/PROVIDER_MANIFEST.json` once and the framework instance copies/rehashes it. Record raw-hash or parser failure; don't turn geometry into physical two-body evidence.

## Framework v1.0.7 contract

The frozen framework runtime is external and untouched. Only newly generated A065-v0.3.1 instance contracts are modified **before** `FREEZE`. `G5 <- G1`, for an actual C++17 FP64 velocity kernel (75/150/300); `G8 <- (G3,G5)`. G6 and G7 remain disabled in cpu profile. The `G2` numerical gate intentionally stays FAIL on legacy 75→150. G3 physical discovery cannot PASS from geometric or scalar toy evidence and remains `NOT_RUN_PREREQUISITE`. `G8` therefore remains blocked for scientific reasons, not an impossible disabled-G7 dependency.

C++ kernel parity covers 1575 components for the three resolutions. This is **kernel-only**; full numerical/backend certification remains open. If the native compiler is unavailable, status is `UNRESOLVED`, never substituted by Python.

## Blindness and reports

Original three sealed sources persist without mutation. Run-level provider manifest, blind results and TeX/PDF stay in a freshly allocated non-overwriting run folder. The PDF's three observable channels and model boundaries are explicit. No physical force calibration or post-hoc tolerances. The private reveal target is separate and absent from public package.