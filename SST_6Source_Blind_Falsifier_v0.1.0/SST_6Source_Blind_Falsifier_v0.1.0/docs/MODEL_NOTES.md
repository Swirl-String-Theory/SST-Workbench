# Model notes and assumptions

## Regularized Biot–Savart kernel

The native kernel uses the declared vortex-blob line element

```text
du = Gamma/(4*pi) * (dl x r) / (|r|^2 + a^2)^(3/2)
```

and the corresponding declared finite-core energy proxy

```text
E = rho*Gamma^2/(8*pi) * double_integral [t(s) dot t(s')] / sqrt(r^2 + a^2) ds ds'.
```

This is a **declared test regularization**, not a claim that the Canon has uniquely derived this core profile.

## Core normalization

When Ridgerunner `thickness` is available, coordinates are divided by that value so the baseline resolved tube radius is approximately `a_core=1`.

## U2 pressure-Poisson diagnostic

For an incompressible field,

```text
S = partial_i u_j * partial_j u_i
```

is the pressure-Poisson source up to the density/sign convention. The code evaluates it by finite differences on nested Cartesian boxes and reports normalized monopole and dipole moments.

## AO gates

The AO gates use geometry-driven perturbation modes and the declared self-induction energy. No thermodynamic temperature is asserted. The optional Boltzmann geometry proxy is explicitly excluded from the primary verdict.

## Rossby gate

The Rossby gate is an analogy diagnostic only. A Gaussian vortex-core gradient supplies `beta_eff`; the self-induced velocity magnitude supplies `U`. The output `chi_R` is not a Canon quantity.

## Kleckner perturbations

Kleckner et al. used transverse RMS displacement `0.25*r0` with smoothing length `0.5*r0`. Identifying rope diameter with `2*a_core` gives the preregistered geometry test values:

```text
RMS = 0.5*a_core
sigma = 1.0*a_core
```

## H5 scale scan

The scale scan changes the centreline homothetically while holding `a_core` and circulation fixed. Values with lambda < 1 are not used in the default campaign because they violate the baseline hard reach constraint by construction.

## Helmholtz calibration

The calibration null is the ordinary second-order susceptibility

```text
chi(omega) = 1 / (omega0^2 - omega^2 - 2 i gamma omega).
```

The ringdown is fitted independently and used to predict the driven peak and phase response.
