# Seven-paper synthesis → SST test architecture

## A. Promote to main-canon methodology/orthodox layer

### A1. General incompressible pressure closure
For constant density and incompressibility,

\[
\nabla^2\left(\frac{p}{\rho_{\!f}}\right)
=\frac12|\boldsymbol\omega|^2-S_{ij}S_{ij},
\qquad
S_{ij}=\frac12(\partial_jv_i+\partial_iv_j).
\]

This is an exact bulk identity of incompressible Euler/Navier--Stokes (constant density). It supersedes use of a local Bernoulli pressure defect as a *general* three-dimensional knot closure. Bernoulli remains valid only under its stated stationary/streamline assumptions.

For a free-space solution with suitable decay,

\[
\frac{p(\mathbf x)-p_\infty}{\rho_{\!f}}
=-\frac{1}{4\pi}\int
\frac{\frac12|\boldsymbol\omega(\mathbf x')|^2-S:S(\mathbf x')}
{|\mathbf x-\mathbf x'|}\,d^3x'.
\]

For periodic numerical domains the Green solver must instead use the periodic Poisson kernel; this package uses the Fourier representation.

### A2. Representation-invariance guard
If two formulations are declared exactly equivalent descriptions of the same on-shell SST state, all physical observables must agree after the correct transformation. A discrepancy is not a new physical effect until it survives continuum/refinement tests and is shown not to scale with incompressibility/Euler residuals.

### A3. Kinematics-versus-dynamics guard
A fitted kinematic ansatz (clock law, dispersion curve, cosmographic H(z), monotone phase warp) is not evidence for the underlying SST dynamics unless the mapping from SST primitives to fitted parameters is derived independently and the derived quantities reproduce from the frozen posterior/solution.

## B. Research-track only

### B1. Topology-layer separation
Maintain distinct labels for:
- material centerline topology `K_center`;
- resolved vorticity-tube topology `K_omega`;
- internal phase-fiber topology `K_phase`;
- observable-null/singularity topology `K_null`.

No equality between these objects is assumed.

### B2. Phase closure and aliasing
For a physical phase observable on a closed carrier,

\[
W_\Phi=\frac{1}{2\pi}\oint d\Phi\in\mathbb Z
\]

must converge under spatial sampling refinement. Finite segmentation generates aliases; a physical mode remains fixed when the number of sampling stations changes, while discretization aliases move with the sampling lattice.

### B3. Spectral certification
A proposed SST precision mode is not certified by one peak. Require:
- resolution convergence;
- perturbation/boundary-sector bookkeeping;
- held-out repetition;
- pseudospectral/conditioning audit where a linearized operator exists;
- dynamic structure factor or equivalent correlation-spectrum check when individual peaks merge.

Article 1's Ising ratios are **not** imported as SST targets.

### B4. Effective metric discipline
An effective metric may only be assigned after derivation of the principal symbol of the linearized probe sector. The metric is a probe-response geometry unless a separate theorem promotes it to substrate geometry. Circulation reversal should be decomposed into even and odd channels before attribution.

### B5. Holonomy discipline
Closed-loop phase/frequency shifts must be repeated with finer representation steps. If the effect vanishes as step size tends to zero, classify it as discretization/transport holonomy. A continuum holonomy requires a nonzero converged loop defect compatible with a local commutator/curvature prediction.

## C. Not imported as SST physics
- acoustic phase-vortex Hopfions;
- nonlinear optical OAM phase plates;
- magnetic-vortex Ellis wormhole metrics;
- acoustic-analogy frequency holonomy;
- Hořava--Lifshitz logarithmic q(z) ansatz.

They serve as falsifier design precedents only.
