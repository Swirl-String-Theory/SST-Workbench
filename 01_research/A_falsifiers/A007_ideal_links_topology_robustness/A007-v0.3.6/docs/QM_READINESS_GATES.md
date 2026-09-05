# QM-readiness gates — v0.3.3

This suite asks whether a classical ideal-link background is sufficiently controlled to justify a
later quantization attempt.  It does not identify topology with quantum state space.

## C0 — numerical continuum gate

Before interpreting a closure, keep `epsilon/D` and the physical self-exclusion arcs fixed and refine N.
The continuum campaign reports length, bending, repulsion, regularized Neumann energy and rigid-motion
residual convergence.  A finite-difference step-halving pass is not a substitute for this spatial gate.

## Q1 — discrete sector labels

All `2^m` circulation assignments are retained.  Pairwise Gauss-linking is integer locked on a
separate topology grid.  Pairwise-zero links are explicitly marked as requiring higher invariants.
For `L6a4`, Borromean identity and catalog `|mu-bar_123|=1` are metadata; the Milnor invariant is not
numerically computed by this release.

## Q2 — classical background candidate

At fixed finite-core regularization, a low normal rigid-motion residual and a low reduced gradient are
necessary.  v0.3.3 additionally probes a trust-limited Newton direction for full/max best sectors.
Only a genuinely stationary constrained solution can promote the Hessian to a stability operator.

## Q3 — reduced quadratic stability

Low-harmonic normal deformations are used after rigid Euclidean gauge removal.  Full off-diagonal
central-difference Hessians are required for a stability claim.  Energy terms use D-dimensionalization,
not per-link or cross-resolution fitted scales.

## Q4 — candidate phase-space form

The Research-Track filament two-form is

\[
\Omega_{ab}=\sum_i\sigma_i\oint \hat{\mathbf t}_i\cdot
(\delta\mathbf X_a\times\delta\mathbf X_b)\,ds.
\]

Rank, nullity and singular vectors are reported.  For a singular form, v0.3.3 supplies an algebraic
image-space quotient, but does not declare kernel directions to be physical gauge modes.

## Q5 — linearized Hamiltonian spectrum

For a full-rank or explicitly projected diagnostic form,

\[
\Omega\dot{\mathbf q}=H\mathbf q.
\]

Only dimensionless spectra and frequency ratios are reported.  No absolute `hbar*omega` spectrum is
claimed without an independently derived action scale and canonical normalization.

## Readiness levels

0. not ready;
1. pair-linking-sector resolved;
2. classical-background candidate;
3. quadratic-stability candidate;
4. candidate-phase-space ready;
5. quantization-readiness candidate.

A v0.4 closure-robustness claim should additionally require a satisfactory C0 continuum ledger.
