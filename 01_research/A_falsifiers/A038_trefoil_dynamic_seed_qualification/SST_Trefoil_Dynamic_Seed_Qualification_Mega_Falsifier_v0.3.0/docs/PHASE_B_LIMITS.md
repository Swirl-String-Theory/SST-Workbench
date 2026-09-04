# What the new Phase B does, and does not, certify

## Implemented

- Full 3N-coordinate central-difference monodromy at three epsilon values.
- A fixed return-group action for every perturbed trajectory: no fresh Kabsch,
  normalization, resampling or volume reset inside the derivative.
- Fixed reference length/volume, RK4 time grid and geometry-guard cadence.
- Bounded 3N-state shooting with period and rotation/translation variables,
  fixed cyclic permutation and SVD-ranked phase conditions.
- Translation/rotation/time-flow generators, numerical invariant-subspace
  leakage, time-neutral residual, quotient eigensystem and residuals.
- Reparametrization diagnosed but not silently removed; scaling is not assumed
  a symmetry. Near a relative equilibrium time flow can be redundant.
- Controlled finite-difference JVP/Arnoldi mode explicitly labelled partial,
  with Ritz residuals and a closed stability gate for the unseen spectrum.
- Paired baseline, identical sham, half-feedback and fixed-core ablation.
  The only intervention is alpha in a=a0*(L0/L)^(alpha/2); the primary outcome
  is change in fixed-group return RMS. Identity, dynamics and time-grid checks
  prevent mismatched controls.
- Full N={64,96,128}, dt-factor={1,.5,.25}, core={.06,.08,.10}, mesh={2.4,4,5.6}
  ladder enumeration, without dropping failed cells.

## Remaining publication requirements

`NUMERICALLY_VALIDATED_AT_DISCRETIZATION` is deliberately not a proof of
stability, a multi-ladder convergence certificate, or evidence for physical SST.

1. Obtain a genuinely accurate trefoil RPO (RMS <=1e-4; period >=1.2), with
   qualified geometry and the frozen S37 gate. A near return is not enough.
2. Converge orbit, period, return action and complete nontrivial spectrum across
   ladders. Current runner enumerates cells but does not implement rigorous
   branch matching, spectral enclosure, or a continuum-limit theorem.
3. Remove only verified symmetry subspaces. Float64 leakage tests are necessary
   diagnostics, not exact proofs; a nonsmooth mesh-cap branch needs care.
4. Bound finite-difference/integration errors. Epsilon agreement and the
   eigenvector-condition sensitivity indicator are NOT rigorous error bounds.
5. Establish topology preservation with segment-level/continuous-time checks or
   an independent certified provider. Initial diagram witnesses and sampled
   vertex distances do not supply that guarantee.
6. Replicate intervention effects, controls and convergence per independent
   construction family; account for within-family dependence and selection.
   The present code keeps causal language disabled even when a panel completes.
7. For external generalization obtain genuinely untouched upstream parents or
   independent datasets. Random perturbations of known parents provide only a
   prospective realization holdout, not parent-level out-of-distribution evidence.

## Provenance and sources

- Fremlin: local immutable `.short` geometry and source provenance. Upstream
  [Fremlin trefoil page](https://david.fremlin.de/knots/3_1.htm).
- Gilbert: local original Fourier coefficients, reconstructed with
  X=A0/2+sum(A_i*cos(i*t)+B_i*sin(i*t)); SONO-derived approximate ideal knots,
  not guaranteed global minimizers. [Author's dataset description](https://katlas.org/wiki/Ideal_knots).
- SST braid: use the local Knot Library v0.2.5 constructor and hash its dependency
  tree; imported braid metadata does not by itself verify embedded geometry.
- Method reuse: fixed-group full-state finite-difference approach in the repo's
  counterpulley and Kelvin monodromy modules. Their two-filament dynamics are
  not transplanted into this one-filament model.
- [SciPy eigs](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.eigs.html)
  supports LinearOperator-based Arnoldi; a requested subset is not the full spectrum.

All conclusions are restricted to the regularized filament / finite-core
surrogate. Fremlin redistribution licensing remains unresolved; the release
shares recipes and hashes, not an upstream-data redistribution license.
