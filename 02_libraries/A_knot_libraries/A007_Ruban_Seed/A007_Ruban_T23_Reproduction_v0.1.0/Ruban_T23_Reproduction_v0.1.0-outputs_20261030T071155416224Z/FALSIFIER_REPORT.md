# Ruban T(2,3) - reproducible falsifier report

## Claim and scope
Attempt to reproduce Ruban (2018), arXiv:1801.04822, equation (9), Fig. 3:
T(2,3), B0=0.154, delta/R0=0.05, Lambda=1.4+0.5 ln(200),
R0=1, Gamma=2*pi, lifetime >300 and distance >1200 R0 for a selected run.

This release is a numerical filament-model reproduction attempt, NOT a solution
of full three-dimensional incompressible Euler nor a test of internal core twist.

## Numerical method
Fourier pseudospectral X_beta/X_betabeta; full O(N^2) Rosenhead-Moore
quadrature including self-contribution at finite delta; Ruban local induction
lambda_tilde/2 * (X_beta cross X_betabeta)/|X_beta|^3;
fixed-step classical RK4; deterministic long-wave perturbations; no artificial
viscosity, smoothing, knot forcing or remeshing. The paper's exact random seed,
finite deformation criterion and integrator implementation are unavailable.

## Limitations and falsifier gates
- G0 provenance/geometry: requires correct seeded T(2,3), parameter data, source SHA.
- G1 solver smoke: ring symmetry, sign, initial convergence, finite field.
- G2 energy + sampling: error must remain below specified bounds.
- G3 duration: T >= 300 dimensionless, with no stop and documented travel.
- G4 parametric window: local B0 scan should show lifetime sensitivity.
- G5 spatial and temporal convergence: compare N=128/256/512 and dt, dt/2
  at identical physical final times, plus a regularization delta sensitivity.
- G6 Ruban published benchmark: adequate paper-matched phase convention,
  numerical method and sustained quasi-stability; require independent audit.
- G7 full Euler/finite core/internal twist: OUT OF SCOPE; NEVER infer from G6.

The operational RMS threshold and sampling-quality stop are new explicit
benchmarks; they are NOT Ruban's unreported termination rule.

## Execution summary
Mode: FULL | timestamp UTC: 20261030T071155416224Z | configuration SHA256: 095324f573860b739aa8d0c3b5ae60c18a1749a4f52d6226bbef4996f6513aed

| B0 | N | dt | attained t | stop reason | relative energy drift | shape RMS | status |
|---:|---:|---:|---:|---|---:|---:|---|
| 0.1400 | 256 | 0.002 | 1.00000 | ENERGY_DRIFT_STOP | 3.182e+10 | 8.321e+04 | UNRESOLVED |
| 0.1480 | 256 | 0.002 | 1.00000 | ENERGY_DRIFT_STOP | 4.052e+10 | 7.051e+04 | UNRESOLVED |
| 0.1520 | 256 | 0.002 | 1.00000 | ENERGY_DRIFT_STOP | 5.663e+08 | 1.458e+04 | UNRESOLVED |
| 0.1540 | 256 | 0.002 | 1.00000 | ENERGY_DRIFT_STOP | 4.029e+08 | 6.065e+03 | UNRESOLVED |
| 0.1560 | 256 | 0.002 | 1.00000 | ENERGY_DRIFT_STOP | 3.946e+07 | 2.369e+03 | UNRESOLVED |
| 0.1600 | 256 | 0.002 | 1.00000 | ENERGY_DRIFT_STOP | 4.668e+06 | 6.707e+02 | UNRESOLVED |
| 0.1680 | 256 | 0.002 | 1.00000 | ENERGY_DRIFT_STOP | 5.496e+06 | 7.593e+02 | UNRESOLVED |

## Result interpretation
A run that survives a short smoke interval is **NOT** evidence for Ruban's >300 lifetime. A long operational survivor is **NOT** certified until convergence and invariants pass.
