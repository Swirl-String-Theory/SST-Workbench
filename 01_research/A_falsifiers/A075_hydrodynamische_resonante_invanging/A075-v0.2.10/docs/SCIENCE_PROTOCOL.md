# Scientific protocol: Ruban T(2,3), exact A007 seed

## Claim and model

Hypothesis H1: for Ruban parameters (R0=1, Gamma=2 pi, delta=1/20, Lambda=7/5+ln(200)/2), there exists a normal-relative-equilibrium for a perturbed T(2,3) geometry within a physically supported B0 interval near 0.154. Hypothesis H2: such an equilibrium has a converged, non-growing physical linear perturbation spectrum. Neither hypothesis is established.

## Implementation

- Operator: source-independent segment-midpoint regularized Biot-Savart integral, coefficient Gamma/(4 pi)=1/2, with local curvature-binormal coefficient (Lambda-ln(R0/delta))/2 = 0.5267132048600137 in dimensionless units.
- Geometry: exact A007 SHA-verified N2048 equal-arclength vertices at B0=0.154, transformed to uniform theta by periodic cubic interpolation; other B0 from analytic torus.
- Residual: weighted L2 norm of normal-component velocity after optimal axial translation and axial rotation. Tangential velocity omitted as geometric reparameterization.
- Shape deformation: finite radial/vertical Fourier harmonics m*q for m>=2, held within amplitude bounds +/-0.035 per coefficient. This restriction MUST NOT be interpreted as full functional minimization.
- Exploratory linearization: finite-difference projected Ritz Jacobian on radial/vertical cos/sin Fourier modes. Lacks correct dynamic gauge quotient; NO stability promotion.

## Required follow-up tests

1. Verify source hashes and analytic torus geometry; cross-check independent physical-unit scaling.
2. Replace source-independent velocity approximation with an independently validated higher-order quadrature and compare error at N=128,256,512,1024 at identical parameters.
3. Vary harmonic count and shape parameterization; obtain a numerically small equilibrium residual independent of basis and resolution.
4. Derive constrained linearized operator with tangent-reparameterization gauge, correct neutral modes, and zero eigenmodes associated with symmetries; test its eigenvalues against finite perturbation growth.
5. If reference orbit is periodic rather than a relative equilibrium, perform Floquet analysis instead.
6. Use at least three resolution and timestep levels at constant final time. Include perturbation amplitude sensitivity, seeded ensembles, Hamiltonian, knot topology, and collision diagnostics.
7. Transfer only converged seeds to A075 3D incompressible Euler with separate explicit finite-core/box/deposition/time/topology qualification.

## Predeclared failure gates

- Missing source or wrong SHA: stop.
- Invalid or self-intersecting mesh: fail geometry gate.
- Optimizer exits with non-small epsilon: no equilibrium claim.
- Changing Ritz basis, finite-difference step, or discretization changes growth sign: no spectral claim.
- Numerical survival without full independent convergence: no physical stability claim.

## Status

Everything released in this extension: DEVELOPMENT_ONLY. No altered A075 G0..G13 or E010 scientific release status.

## References

```latex
\bibitem{Ruban2018LongLived}
V. P. Ruban (2018),
``Long-lived quantum vortex knots,''
JETP Letters 107, 307--311.
https://doi.org/10.1134/S0021364018050120

\bibitem{Ruban2018QuasiStable}
V. P. Ruban (2018),
``Quasi-stable configurations of torus vortex knots and links,''
Journal of Experimental and Theoretical Physics 127, 581--586.
https://doi.org/10.1134/S106377611809008X
```
