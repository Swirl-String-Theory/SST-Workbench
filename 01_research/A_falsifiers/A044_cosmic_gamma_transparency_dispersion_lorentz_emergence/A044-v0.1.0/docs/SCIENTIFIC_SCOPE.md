\
# Scientific scope — v0.1.0

## Frozen blind question

Given published 95% confidence bounds on subluminal photon-dispersion models of the form

\[
p^2 = E^2\left[1+\left(E/E_{\rm LIV,n}\right)^n\right],\qquad n\in\{1,2\},
\]

which model classes retain a non-empty parameter interval when the Carpet 300 TeV transparency requirement is combined with pre-existing time-of-flight, Breit–Wheeler spectral and (where applicable) birefringence constraints?

## What v0.1.0 does

1. Freezes a public, provenance-tagged numerical constraint set.
2. Uses native C++ kernels for dimensionless dispersion parameters, interval intersection, Poisson observability and \(k\ell\).
3. Separates birefringent and non-birefringent linear model classes instead of incorrectly applying a framework-dependent polarization bound universally.
4. Produces a blind verdict before any SST constants are loaded.
5. Verifies a SHA-256 commitment to the private reveal payload.
6. On reveal, tests only explicit SST mapping hypotheses; it does not fit SST constants to the astrophysical data.

## What v0.1.0 does not claim

It is not an independent reproduction of the complete redshift-dependent EBL+CMB+radio optical-depth integral, detector response, intrinsic GRB spectrum, or Carpet event likelihood. Those require source data and model tables beyond the compact published bounds bundled here. Therefore the primary v0.1.0 verdict is a **constraint-space qualification gate**.

## Falsifiable SST reveal hypotheses

- **H_Rc_UV:** \(r_c\) is a universal photon propagation cutoff producing an unsuppressed \(O(1)\) correction in \(k r_c\) or \((k r_c)^2\).
- **H_Swirl_LIV:** \(\hbar\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}/r_c\) directly equals the LIV scale.
- **H_Emergent:** an independently derived SST photon/eigenmode dispersion law produces coefficients inside a surviving blind interval while satisfying polarization and time-of-flight nulls.

Only H_Emergent can keep the full SST photon-propagation closure open after v0.1.0.
