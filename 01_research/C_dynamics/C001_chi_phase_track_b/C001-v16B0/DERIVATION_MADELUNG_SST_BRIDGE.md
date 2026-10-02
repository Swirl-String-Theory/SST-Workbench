# Derivation: conditional Madelung-SST bridge for A=B=C

## Status

**DERIVED-CONDITIONAL / G5 AUDIT.**

The single-modulus condition `A=B=C` is not a numerical fit and not a free
shape tuning. It follows algebraically once the resolved SST core is accepted
as a single coherent Madelung/GP envelope with one transverse stiffness and a
healing-length normalized depletion term.

This file therefore **does not close Gate G5 from pre-existing SST filament
canon alone**. It closes the algebraic part of G5 conditionally:

```text
single-modulus Madelung core envelope accepted
  -> A=B=C
  -> unit GP/NLSE vortex ODE
  -> alpha_ring^GP = 1.6193509...
```

The remaining first-principles question is whether the single-modulus Madelung
core envelope is itself a canon axiom/theorem of SST or remains an effective
resolved-core model.

---

## Local-core commitments used

| # | Commitment | Status |
|---|---|---|
| A1 | Resolved SST core admits one coherent complex envelope `Psi = F exp(iTheta)` | local-core axiom / must be accepted or derived |
| A2 | Vortex phase has quantized circulation `Theta = n theta` | SST-compatible topological input |
| A3 | Depletion energy is represented by a quadratic/quartic local compressibility term and normalized by the physical healing length `xi` | GP/Madelung resolved-core assumption |

These are not pure consequences of ordinary classical Euler vortex-filament
kinematics. They are the additional local-core commitments needed to upgrade
Track B from an imported GP analogy to a derived result inside the resolved-core
sector.

---

## Step 1: Madelung envelope identity

For a coherent quantum-superfluid core, write

```text
Psi = F exp(i Theta),          F = sqrt(rho/rho0).
```

The gradient norm splits identically as

```text
|grad Psi|^2 = |grad F|^2 + F^2 |grad Theta|^2.
```

For a unit straight vortex with `Theta = n theta`, this becomes

```text
|grad Psi|^2 = F'(r)^2 + n^2 F(r)^2/r^2.
```

This identity is the solid part of the argument. Once a single complex envelope
is admitted, the radial-amplitude and azimuthal-phase gradient terms share the
same stiffness.

---

## Step 2: A=B from the Euclidean gradient norm

The generic radial density is

```text
L_r = A F'^2 r + B n^2 F^2/r + (C/2)(F^2-1)^2 r.
```

The one-envelope kinetic/quantum-pressure term gives, up to one common factor,

```text
|grad Psi|^2 r = F'^2 r + n^2 F^2/r.
```

Therefore

```text
A = B.
```

This part is algebraic. A purely classical fluid without the quantum-pressure
`|grad F|^2` term would not yield this equality and does not supply a smooth
Madelung vortex core of the same type.

---

## Step 3: C=A from healing-length normalization

Write the physical local core energy in abstract stiffness form:

```text
E_perp = integral [ kappa |grad Psi|^2 + (lambda/2)(1-|Psi|^2)^2 ] d^2x.
```

The healing length is the physical balance scale

```text
xi^2 = kappa/lambda.
```

With `rho = xi r`, the radial energy becomes, up to the common factor `2*pi*kappa`,

```text
E_perp proportional to integral [ F'^2 r + n^2 F^2/r + 1/2 (F^2-1)^2 r ] dr.
```

Thus in the dimensionless healing-length units

```text
C/A = lambda xi^2/kappa = 1,
```

and therefore

```text
C = A.
```

This is a normalization theorem inside the GP/Madelung resolved-core model. It
is not an independent proof that the SST filament canon must possess this exact
single-envelope compressibility law; that is the explicit G5 commitment.

---

## Derived conditional theorem

Under A1--A3,

```text
L_r = F'^2 r + n^2 F^2/r + 1/2(F^2-1)^2 r    (A=B=C=1).
```

The Euler--Lagrange equation for `n=1` is

```text
F'' + F'/r - F/r^2 + F(1-F^2) = 0.
```

The corrected ring constant extracted by v12B.0 is

```text
alpha_ring^GP = 1.6193509...
beta_ring^GP(q=0) = 0.6193509...
```

This number is a pure dimensionless constant of the unit GP/NLSE vortex ODE. It
does not depend on the numerical value of `xi`, but the physical identification
of `xi` with any SST core radius remains a separate gate.

---

## Remaining open gates

| Gate | Status | Content |
|---|---|---|
| G5 | conditionally closed | closed only after accepting or deriving A1--A3 as SST resolved-core canon |
| G6 | open | structural proof of the numerical proximity `alpha_ring ≈ phi` |
| G7 | open | physical mapping between healing length `xi` and SST core radius `r_c` |
| G8 | open | any bridge from `alpha_ring` to the fine-structure/shielding-gate constant `alpha_fs` |

Recommended wording:

```text
alpha_ring^GP = 1.6193509... is derived within the single-modulus
Madelung resolved-core sector. It is not yet derived from pre-existing SST
filament axioms without the local-core commitment A1--A3.
```
