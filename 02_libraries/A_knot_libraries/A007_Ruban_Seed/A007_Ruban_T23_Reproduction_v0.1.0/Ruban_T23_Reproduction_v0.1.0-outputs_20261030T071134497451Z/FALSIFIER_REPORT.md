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
Mode: BASIC | timestamp UTC: 20261030T071134497451Z | configuration SHA256: 1dc67ae69e4fab28b8bcb321af1ce473de25c8c892ca945f6100f83ea98a1a62

| B0 | N | dt | attained t | stop reason | relative energy drift | shape RMS | status |
|---:|---:|---:|---:|---|---:|---:|---|
| 0.1400 | 128 | 0.002 | 0.50000 | TIME_LIMIT | 5.368e-05 | 3.038e-02 | UNRESOLVED |
| 0.1540 | 128 | 0.002 | 0.50000 | TIME_LIMIT | 8.377e-04 | 7.344e-03 | UNRESOLVED |
| 0.1700 | 128 | 0.002 | 0.20000 | ENERGY_DRIFT_STOP | 1.724e-03 | 4.539e-02 | UNRESOLVED |

## Result interpretation
A run that survives a short smoke interval is **NOT** evidence for Ruban's >300 lifetime. A long operational survivor is **NOT** certified until convergence and invariants pass.
