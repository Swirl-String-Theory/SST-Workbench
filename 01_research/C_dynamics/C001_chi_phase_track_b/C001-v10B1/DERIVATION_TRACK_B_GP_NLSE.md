# Derivation note: Track B v10B.1 — corrected GP/NLSE energy coefficient

## 1. ODE and energy must be mutually consistent

v10B.0 solved the dimensionless GP/NLSE vortex ODE

```text
F'' + (1/r)F' - F/r^2 + F(1-F^2) = 0.
```

The corresponding radial energy density, in units of
`pi rho0 (hbar/m)^2`, is

```text
F^2/r + F'^2 r + lambda (F^2-1)^2 r.
```

Varying the last term gives an ODE contribution

```text
2 lambda F(F^2-1).
```

The ODE contains

```text
F(1-F^2) = -F(F^2-1),
```

so the Euler-Lagrange equation matches only when

```text
2 lambda = 1  ->  lambda = 1/2.
```

Therefore the consistent GP/NLSE energy is

```text
F^2/r + F'^2 r + 1/2 (F^2-1)^2 r.
```

v10B.0 used `1/4`, which corresponds to a different ODE coefficient.

## 2. Core constant

Define

```text
C_GP(R) = integral_0^R [F^2/r + F'^2 r + 1/2 (F^2-1)^2 r] dr - ln R.
```

The ring-energy convention is

```text
E_ring = rho Gamma^2 R/2 [ ln(8R/xi) - alpha_ring ].
```

The hollow-core outer constant is `alpha=2`, hence

```text
alpha_ring_GP = 2 - C_GP.
```

For fixed core radius (`q=0`), v8 gives

```text
beta_ring_GP = alpha_ring_GP - 1.
```

## 3. Algebraic tail

The GP vortex amplitude has an algebraic far-field expansion, not an
exponential convergence law. Schematically,

```text
F(r) = 1 - 1/(2r^2) + O(r^-4).
```

Thus v10B.1 fits

```text
C_GP(R) = C_inf + A/R^2 + B/R^4
```

and reports

```text
alpha_inf = 2 - C_inf.
```

## 4. Consequence

The v10B.0 result `alpha≈1.867` is a coefficient artifact. With the
energy term consistent with the ODE, Track B gives approximately

```text
alpha_ring_GP ≈ 1.619,
beta_ring_GP(q=0) ≈ 0.619,
```

close to the legacy NLS notebook pair `(1.61, 0.61)`.

This is not locked CANON yet; it is a strong Research Track result requiring
normalization and literature-convention audit.
