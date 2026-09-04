# Method

The dynamical state contains the carrier components plus `N_B` closed thread loops. All nonzero-circulation components evolve together under the same regularized filament Biot-Savart + local induction solver. There is no imposed `Omega x r`, no viscosity, no auto-relax, no mutual friction, and no reconnection rule.

Twist-knot threading axes are found geometrically by a finite Fibonacci-sphere search through the carrier centroid. Candidate axes must have finite centerline clearance and a nonzero near-integer Gauss-link probe. This prevents assuming the PCA z-axis is the central hole.

For the analytic torus family a central thread has linking number approximately 2 with `T(2,q)`. For the `T(3,3)` triple-link proxy it links each of the three unknot components approximately once.

Carrier stability diagnostics quotient rigid translation, rigid rotation and tangential marker gauge. Thread motion itself is not rewarded; only its effect on the carrier enters the self-confinement score.

Pressure is reconstructed from the velocity-gradient Poisson source on a periodic numerical box. This is a reduced coarse-graining diagnostic, not a proof of an unbounded-domain pressure monopole.
