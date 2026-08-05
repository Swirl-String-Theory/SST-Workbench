# Methods and limitations v0.2

## Resolving the implicit `.fseries` harmonic origin

Legacy `.fseries` files do not include an explicit harmonic index. Both interpretations are constructed:

\[
\mathbf X_0(t): j=0,1,\ldots,M-1,
\qquad
\mathbf X_1(t): j=1,2,\ldots,M.
\]

If a same-stem `.short` polygon exists, all curves are resampled to normalized arclength. For each candidate the package minimizes RMSD over:

- translation;
- uniform scale;
- rigid rotation in `SO(3)`;
- cyclic phase shift;
- parameter reversal.

It does not permit a mirror reflection. The candidate with the lower discrepancy is selected. A confidence ratio compares the rejected and accepted RMSDs.

This is necessary because an all-zero first six-column row may be either:

1. an explicit zero-valued `j=0` translation row; or
2. a genuine zero-valued `j=1` harmonic forced by symmetry.

Numeric zero spelling (`0`, `0.000`, `0.000000`, signed zero) is not used to infer the index.

## Representation hierarchy

When both representations exist, the default master row uses `.short` as the selected static polygon because it is the directly stored shortened curve. The analytic `.fseries` reconstruction is retained as an independent representation and used for arbitrary-resolution convergence.

Cross-representation shape agreement is computed after removing scale. Therefore a strong shape match can coexist with a non-unit raw length ratio.

## Geometry computation

Both source types are periodically resampled to uniform polygonal arclength before the shared geometry pipeline is run. The C++17 backend accelerates nonlocal-distance, writhe/ACN, intercomponent-distance, and linking calculations.

Reported nonlocal distance, reach, writhe, ACN, and linking quantities remain resolution-dependent numerical proxies.

## Topology boundary

The package preserves directory and filename labels and can merge user metadata. It does not independently calculate Alexander, Jones, or HOMFLY-PT polynomials. Filename agreement and `.fseries`/`.short` shape agreement do not constitute a certified knot-type proof.

## Ridgerunner boundary

Exports are intended as seeds for the existing KnotPlot/Ridgerunner route. Ridgerunner's own thickness, strut set, residual, equilateralization, topology, and convergence evidence remain authoritative for a polished ideal-knot claim.

## Dynamic boundary

Static source files do not encode temporal phase coherence, Goldstone modes, non-affine evolution, defect percolation, or lifetime. Those quantities are only computed by the separate NPZ trajectory route.
