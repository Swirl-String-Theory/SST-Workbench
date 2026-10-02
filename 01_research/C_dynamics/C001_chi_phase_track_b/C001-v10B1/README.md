# SST chi-phase package v10B.1 — Track B: corrected GP/NLSE vortex-ring constant

## Summary

v10B.1 patches v10B.0 by making the GP/NLSE energy functional consistent
with the ODE that is actually solved.

Solved ODE:

```text
F'' + F'/r - F/r^2 + F(1-F^2) = 0,
F(0)=0, F(inf)=1.
```

For an energy term

```text
lambda * (F^2 - 1)^2 * r,
```

variation gives an ODE nonlinear coefficient `2*lambda`. Therefore the
ODE above requires:

```text
lambda = 1/2.
```

v10B.0 used `lambda = 1/4`, which is inconsistent with the ODE and shifted
`alpha_ring` upward to about `1.867`.

## Key result

With the corrected energy density

```text
F^2/r + F'^2*r + 1/2*(F^2-1)^2*r,
```

v10B.1 obtains at finite cutoff `R=12 xi`:

```text
alpha_ring_GP(R=12 xi) ≈ 1.61763,
beta_ring_GP(q=0)     ≈ 0.61763.
```

With an algebraic-tail extrapolation

```text
C_GP(R) = C_inf + A/R^2 + B/R^4,
alpha_inf = 2 - C_inf,
```

the default run gives approximately:

```text
alpha_ring_GP(inf) ≈ 1.61935,
beta_ring_GP(inf)  ≈ 0.61935.
```

This is close to the legacy notebook NLS target:

```text
(alpha_ring, beta_ring) = (1.61, 0.61).
```

## Why this matters

v10A.0 showed that incompressible Euler/Biot-Savart smooth cores give
`alpha_ring ≈ 1.50`, not the NLS value. v10B.1 shows that adding the full
GP/NLSE core energy — density depletion plus gradient plus interaction —
shifts the result close to the legacy NLS constant.

So Track B is now a genuinely positive Research Track result:

```text
Euler Track A: smooth cores       -> alpha_ring ~ 1.50
GP/NLSE Track B: corrected energy -> alpha_ring ~ 1.619
legacy NLS note                   -> alpha_ring ~ 1.61
```

## Epistemic status

Research Track / CANON-compatible effective-core model.

Do not yet mark as locked CANON. Remaining gates:

1. Verify the GP/NLSE normalization convention against the literature or the
   original notebook derivation.
2. Stabilize the asymptotic extrapolation and document the algebraic vortex tail.
3. Keep `alpha_ring` separate from the fine-structure constant `alpha_fs` and
   the orthodox string-theory Regge slope `alpha_prime`.

## Run

```bash
python simulate_chi_phase_v10B1.py
```

Optional:

```bash
python simulate_chi_phase_v10B1.py --r-right 100 --r-eval 15.5 --tol 1e-9
```

## Exports

- `chi_v10B1_core_constants.csv`
- `chi_v10B1_core_constants_v10B0_coeff_comparison.csv`
- `chi_v10B1_convergence.csv`
- `chi_v10B1_asymptotic_fit.csv`
- `chi_v10B1_profile_comparison.csv`
- `chi_v10B1_euler_benchmark.csv`
- `chi_v10B1_energy_consistency.csv`
- `chi_v10B1_convergence.png`
- `chi_v10B1_run_results_summary.txt`
