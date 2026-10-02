# v0.1.3 Patch Notes

## Trigger

The first STANDARD C++ run showed:

- good spinor Hopf convergence;
- excellent geometric preimage linking;
- a significantly weaker director/Coulomb route;
- H1/H3 still passing because the old `0.20` tolerances were too permissive.

## Changes

1. Fourth-order director curvature (`director_curvature_b_fourth_order`) in Python and C++.
2. Explicit FFT Hodge projection before Coulomb reconstruction.
3. `delta_longitudinal` plus raw/projected divergence and projected curl diagnostics.
4. H1/H3 qualification tiers:
   - `STANDARD_PASS`;
   - `CERTIFIED_PASS`;
   - `FAIL`.
5. Independent H3 residuals for integer, spinor and director comparisons.
6. Exact seam endpoint tests modulo U(1).
7. H5 classification:
   - `IDENTITY_BENCHMARK_PASS`;
   - `SST_BRIDGE_PASS`.
8. Runtime/backend provenance.
9. Dedicated high-resolution/convergence CMD runners.

## Expected regression at N=64

On the user-supplied analytic benchmark, the Python reference path should move the director estimate from the old second-order value near `0.8429` to roughly `0.9791`, while keeping the direct spinor result near `0.9518`.

This is a numerical-method improvement, not new physical evidence.
