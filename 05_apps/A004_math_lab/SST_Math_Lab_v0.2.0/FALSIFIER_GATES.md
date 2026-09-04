# SST Math Lab v0.2.0 — Falsifier gates

## G0 — Parse / closure gate
A dataset must contain at least four finite XYZ points and define a nonzero closed polygonal length.

## G1 — Uniform-resampling gate
Curvature/torsion conclusions should persist under increasing uniform arclength sample count.

## G2 — Geometry gate
Track `L/r_c`, extrema/RMS of `kappa r_c`, and `tau r_c`. Large changes with sample count indicate derivative noise or under-resolution.

## G3 — Finite-core Biot–Savart gate
Track `mean |v_BS|`, `max |v_BS|`, `max |v_shape|` versus physics-point count and `a_core/r_c`.

A claimed physical effect that disappears under modest resolution changes is not robust.

## G4 — Incompressibility gate
Use

`R_div = RMS(div v) / RMS(||grad v||_F)`.

Require convergence downward with physics resolution / pressure-probe refinement. The exact acceptable tolerance is campaign-dependent and is not hard-coded as an SST truth criterion.

## G5 — Pressure-Poisson gate
Track the spatial structure and scale of

`nabla^2 p = -rho_f partial_i v_j partial_j v_i`.

The source must converge with pressure-probe step and physics resolution before physical interpretation.

## G6 — Frame gate
Record raw parallel-transport holonomy and verify that results are not caused by Frenet-frame sign flips. Stability uses the periodic corrected transport frame.

## G7 — Linear-regime gate
Enable the epsilon ladder. Reject a stability number as unresolved if the growth-rate spread across `epsilon/2, epsilon, 2 epsilon` is large.

## G8 — Mode-ceiling gate
Increase the normal/binormal Fourier ceiling `M`. A physically relevant leading growth rate should approach a plateau rather than drift without convergence.

## G9 — Frozen-geometry stability gate
For the reduced Jacobian `A`, inspect the complex spectrum.

`max Re(lambda) > 0` is evidence for an instantaneous growing component of the chosen regularized filament model at that frozen geometry.

It is **not** by itself evidence that a moving/rotating/periodic knot is globally unstable.

## G10 — RPO/Floquet upgrade gate
The decisive later test is a co-moving or relative-periodic solution plus monodromy/Floquet multipliers. v0.2.0 intentionally labels its result as pre-Floquet.
