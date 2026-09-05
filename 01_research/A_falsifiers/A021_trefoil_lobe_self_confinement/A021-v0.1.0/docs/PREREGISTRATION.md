# Preregistered hypothesis and falsification gates

## Hypothesis H_LOBE

For a relaxed trefoil, the three mutually tilted lobes produce an orientation-dependent **non-local Biot–Savart contribution** that reduces unstable intrinsic shape motion and, at the closest cross-lobe approach, contributes a separating normal velocity.

This package does **not** insert repulsion, contact forces, collision constraints, or reconnection. The only centerline dynamics used in the primary test is a Rosenhead-type finite-core regularized Biot–Savart kernel.

## Blinding

1. Both source curves are loaded and normalized to the same total arclength.
2. A fixed seed randomly maps them to `B01`, `B02`.
3. All primary metrics, controls, gate decisions and `pre_unblind/blind_verdict.json` are written using only blind IDs.
4. Only then is `unblind_manifest.json` written.

No threshold depends on source identity.

## Fixed-core calibration

The source files have arbitrary coordinate scale. To represent one fixed physical SST core without tuning either source, each blind geometry is first normalized to total arclength `2*pi`. Its robust tube-thickness estimate is then computed as the minimum of a low-quantile local curvature radius and half a doubly-critical self-distance estimate. The numerical core is preregistered as `0.90 * thickness`. Physical scaling is finally chosen so that this numerical core equals the canonical `r_c`. The rule is identical for B01 and B02 and is applied before unblinding.

## Decomposition

At centerline sample `i`, induced velocity is split into

- `local`: segments within the preregistered cyclic local span;
- `same_lobe`: non-local segments assigned to the same lobe;
- `cross_lobe`: non-local segments assigned to either of the other two lobes;
- `transition`: segments crossing a lobe-label boundary.

The exact numerical identity `total = local + same_lobe + cross_lobe + transition` is gate G0.

## Shape reduction

Rigid translation and rotation are least-squares fitted and removed. Tangential velocity is then removed because it changes filament parameterization rather than centerline shape. The resulting normal field is the intrinsic shape velocity.

Six preregistered deformation modes are generated geometrically and orthonormalized:

- three lobe-tilt symmetry modes;
- three lobe-breathing symmetry modes.

For each mode `phi_b`, the package evaluates `X + eps phi_b` and `X - eps phi_b` and forms the central-difference reduced Jacobian

`J_ab = <phi_a, [V_shape(X+eps phi_b)-V_shape(X-eps phi_b)]/(2 eps)>`.

The same construction is performed for each velocity decomposition component.

## Gates

- **G0 numerical sanity:** split closure and core-clearance prerequisites pass.
- **G1 relative equilibrium:** base intrinsic shape speed is small relative to total induced speed. Diagnostic, not a critical overall gate.
- **G2 reduced stability:** reduced Jacobian maximum real eigenvalue is small relative to its spectral scale and converges across epsilon levels.
- **G3 cross-lobe stabilizes:** removing the cross-lobe Jacobian makes the maximum real growth rate worse by the preregistered amount, and the cross-lobe Jacobian is not negligible.
- **G4 nearest-pair cross separates:** at the closest pair belonging to different lobes, the cross-lobe contribution gives positive distance rate.
- **G5 orientation specificity:** deterministic matched lobe-orientation scrambles degrade the stability metric. Diagnostic in v0.1.0.
- **G6 nonlinear ringdown bounded:** a finite lobe-tilt perturbation remains bounded and never enters the near-core event threshold.

Critical overall gates are G0, G2, G3, G4, G6. Both independent source geometries must pass for overall `PASS`.

## Circle null

A perfect circular unknot with the same normalized arclength and finite-core kernel is tested for mean radial velocity. The null expectation is approximately zero radial collapse. Failure of this null makes the campaign `INCONCLUSIVE` because it indicates a solver/discretization artifact relevant to the physical hypothesis.

## Pressure-Poisson diagnostic

The extended configuration optionally evaluates a periodic-box FFT solution of

`laplacian(p/rho) = - sum_ij (partial_i v_j)(partial_j v_i)`.

This is **diagnostic only**. It is not added to the filament update because pressure acceleration and filament advection are different dynamical objects. Boundary conditions are periodic and therefore not claimed as an isolated free-space pressure solution.
