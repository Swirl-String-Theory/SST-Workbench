# CANON status — v10B.1

Status: **Research Track / CANON-compatible effective-core model**.

Canon-safe result:

```text
For the GP/NLSE ODE
F'' + F'/r - F/r^2 + F(1-F^2)=0,
the consistent energy interaction coefficient is 1/2, not 1/4.
```

Research Track result:

```text
alpha_ring_GP ≈ 1.619,
beta_ring_GP(q=0) ≈ 0.619,
```

which is close to the legacy NLS notebook target:

```text
(alpha_ring, beta_ring) = (1.61, 0.61).
```

Do not conflate:

- `alpha_ring`: vortex-ring energy intercept.
- `alpha_fs`: electromagnetic fine-structure/shielding-gate constant.
- `alpha_prime`: Regge slope in orthodox string theory.

Open gates before CANON lock:

1. Independent normalization audit of the GP/NLSE functional.
2. Literature comparison for the NLS vortex-ring constant and radius convention.
3. Higher-resolution convergence and tail-fit stability checks.
