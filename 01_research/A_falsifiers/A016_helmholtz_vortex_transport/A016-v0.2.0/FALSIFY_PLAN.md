# A016 v0.2.0 falsification plan

## Primary split

The experiment separates two questions that were entangled in v0.1.1:

1. **Does a candidate closed vortex geometry behave as a viable relative equilibrium?** — H0-H4.
2. **What does ideal incompressible transport imply about the material vorticity population and its exterior field?** — P0-P6.

Failure of (1) does not logically invalidate measurements in (2), so the DAG is intentionally parallel after infrastructure/reference validation.

## Gate families

### Infrastructure

- G0: frozen protocol integrity.
- G1: external source admissibility/provenance.
- G2: self-contained Python FP64 numerical controls.
- B0: strict C++/OpenMP FP64 parity certification.

### Original Helmholtz/static-centerline family

- H0: closed geometry + thickness precondition.
- H1: resolution convergence.
- H2: meridian circulation versus linking.
- H3: relative equilibrium after removing translation, rigid rotation, and tangential reparameterization.
- H4: orientation/circulation reversal + mirror covariance.

### Material-population family

For the exact volume-preserving affine map

\[
\mathbf{F}(t)=\operatorname{diag}\!\left(e^{at},e^{-at/2},e^{-at/2}\right),
\qquad \det\mathbf{F}=1,
\]

P0 checks the Cauchy map

\[
\boldsymbol{\omega}(t)=\mathbf{F}(t)\boldsymbol{\omega}_0,
\]

including the implication

\[
\boldsymbol{\omega}_0=0\iff \boldsymbol{\omega}(t)=0
\]

for invertible \(\mathbf F\). P1 checks material-volume conservation. P2 checks reciprocal stretching of vorticity magnitude and cross-sectional area so that vorticity flux remains fixed.

### Exterior matter-field family

- P3: local exterior `div u ~ 0` and `curl u ~ 0` while `|u| > 0`.
- P4: nontrivial circulation periods in the multiply connected exterior.
- P5: deterministic finite-core kinetic-energy fraction outside a near-core source mask.
- P6: far-field velocity power-law classification on nonzero-vector-area closed sources.

The P6 velocity exponent is frozen before post-run mechanism comparison. Under a steady irrotational Bernoulli map, a measured \(|\mathbf u|\sim r^{-p}\) implies \(|\nabla p|\sim r^{-(2p+1)}\). This relationship is reported rather than used to tune \(p\).

## Falsification discipline

- Original H0-H4 thresholds are unchanged from v0.1.1.
- No scientific gate terminates a sibling gate.
- Source/compiler failures are separated from physical failures.
- Ineligible P6 geometries are not coerced into PASS or FAIL.
- The next stronger version should use time-dependent Euler/finite-core trajectories and material tracers rather than infer temporal persistence from static centerlines.
