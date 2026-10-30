# Ruban v0.1.0 validation ledger

## Full reproduction claim

Author's target: 2018 JETP Letters, arXiv:1801.04822v2, Figure 3 at t=320, B0=0.154, Lambda=1.4+0.5*ln(200), delta/R0=0.05. The article reports knot lifetime >300, axial displacement >1200 R0, and Hamiltonian preserved to at least 7 decimal places. In this package, meeting these three paper comparisons is necessary but NOT sufficient without spatial and temporal convergence and a scientifically matched deformation criterion.

## Computation status as of this release

- Source PDF equations cross-checked with published Figure 3 and dimensionless equation (9).
- Original user file SHA256 locked in source and machine manifest.
- Solver tests pass (7/7), ring positive axial propagation confirmed.
- N=256 / dt=0.001 / t=1 / B0=0.154: operational limit reached without stop; relative Hamiltonian drift=1.903e-5.
- N=128 / dt=0.002 / t=0.5 / B0=0.170: stopped at t=0.2 due to energy drift; this is NOT a physical-stability failure.
- At t=0.03, delta=0.05, dt vs dt/2 geometric differences around 4.7e-10; N=64 vs 128 difference 0.004005 and N=128 vs 256 difference 0.001423 (normalized R0). This suggests improvement but does not close convergence.
- delta=0.025 changes shape; finite-regularization effects not ruled out.
- No full T=320 run performed; G3-G6 remain UNRESOLVED.

## Stop interpretation

`TIME_LIMIT`: finished requested numerical window, not a finding of physical stability.
`ENERGY_DRIFT_STOP`: numerical run invalid before physical interpretation.
`SAMPLING_QUALITY_STOP`: parameter mesh has become under-resolved; no physical implication.
`OPERATIONAL_DEFORMATION_STOP`: provisional model-specific shape threshold crossed, not identical to Ruban's unpublished criterion.
`NONFINITE_FIELD` and `DEGENERATE_GEOMETRY`: numerical failure.

## Necessary follow-on studies

1. Frozen 256-point seed and zero/controlled perturbation check.
2. N=128,256,512 at identical t=1, 10, 100 and later 320, with dt refinement (at least two scales).
3. Track relative energy error, segment spacing, characteristic speed, nonlocal clearance, and mean z travel at every finite physical checkpoint.
4. Around B0=0.154 scan increments <=0.002, then <=0.0005 inside candidate windows; repeat for independent smooth perturbation seeds. Stop if observational threshold is numerically polluted.
5. Repeat delta/R0=0.05 and 0.025 with identical Lambda and adequate quadrature; do not infer core-scale convergence from regularization changes.
6. Check ring benchmark against asymptotic thin-ring velocity and compare a second discretization/integrator.
7. Reproduce Figure 3 geometry at t=320 (account for axial translation, rotation and phase), comparing relative shapes rather than pixel impressions.
8. Only after above qualifies the filament surrogate should full Euler finite-core and twist experiments begin.

No twist/parallel background field is introduced in this first Ruban-only falsifier, by design: otherwise the paper cannot be independently reproduced.
