# A054 v0.2.0 certification protocol

## Question
Can a three-component linked nucleon candidate that survived A054-v0.1.1 remain dynamically admissible under finite-core perturbations, a transverse Kelvin/torsion-sensitive mode basis, nonlinear return tests, and—only when an RPO is independently detected—a relative Floquet return map?

## Hard certification path

1. **C0 Jacobian epsilon convergence** — the projected finite-difference generator must converge under the preregistered perturbation ladder.
2. **C1 Relative-equilibrium residual** — diagnostic only. It is recorded for every case, but excluded from hard certification so v0.1.1 cluster values cannot be converted into a post-hoc pass threshold.
3. **C2 Restoring/bounded response** — symmetric ± centroid-separation perturbations must remain bounded and must not collapse inter-component clearance.
4. **C3 Kelvin local boundedness** — after quotienting rigid translation/rotation and tangential marker motion, the normalized worst local growth rate must remain below the frozen method threshold.
5. **C4 Nonlinear ringdown boundedness** — perturbation along the least-stable resolved mode must remain bounded, topology-preserving, and free of a near-collapse clearance event.

Passing the hard subset C0, C2, C3 and C4 yields `CERTIFIED_RESTORING_KELVIN_RINGDOWN_BRANCH`. C1 is not part of that conjunction.

## Conditional RPO/Floquet path

`C5_RPO_recurrence` is a nontrivial recurrence test. A trajectory must first leave the initial shape, then return after a finite excursion while preserving topology and clearance.

Only after C5 passes is the nonlinear time-T relative return map finite-differenced. Component-wise tangential marker velocity is removed as gauge during the evolution. The unperturbed relative group action (component cyclic relabels + global SE(3)) is held fixed while differentiating the perturbed endpoints. Inputs and outputs are restricted to the preregistered physical mode subspace. One multiplier nearest unity is treated as the candidate phase-neutral direction; the largest remaining modulus is compared with the frozen `floquet_spectral_radius_max`.

No accepted RPO means `C6_projected_relative_Floquet_bounded = null` and the Floquet layer is `NOT_EVALUATED_NO_RPO`. The code therefore never manufactures a Floquet PASS from a local Jacobian.

Passing the hard dynamical gates plus C5 and C6 yields `CERTIFIED_RPO_PROJECTED_FLOQUET_BRANCH`. This certifies only the resolved projected return map, not the full infinite-dimensional Euler operator.

## Mode basis

The blind runner constructs only geometry-derived modes:

- three compensated centroid-separation modes;
- one breathing mode per component;
- one curvature-windowed binormal **torsion-sensitive centerline** mode per component;
- normal/binormal Kelvin-like Fourier modes for the preregistered harmonics.

The torsion-sensitive modes are centerline perturbations only. They are not an independent Cosserat/material-twist degree of freedom.

Rigid translation, rigid rotation and component-wise tangential reparameterization are projected out before orthonormalization.

## Energy-Hessian diagnostic

A regularized mutual-filament energy Hessian is recorded in the reduced separation subspace. It is **diagnostic**, not by itself a hard stability proof: inviscid vortex dynamics is first-order/Hamiltonian, so positive energy curvature alone is neither necessary nor sufficient for full dynamical stability.

## Spatial convergence

The local generator/restoring observables are evaluated over a preregistered `N` ladder. Time steps obey `dt ∝ N^-2` while each probe keeps constant `T_final`. Failure of the spatial summary tolerances produces `INCONCLUSIVE_NUMERICAL`, never a physical FAIL.

## Blindness

Preparation knows the semantic geometry and chooses the preregistered cohort. The isolated certification runner receives only `CAND_<hash>.npz`, anonymous IDs, a frozen config and a SHA-256 commitment to the private mapping. It contains no skeleton, nucleon, or 5_2/6_1 labels.
