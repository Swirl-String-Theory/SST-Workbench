# Science contract — Borromean WHOLE v0.4.2

## Claim boundaries

1. Geometric placement of three **whole** near-circle v0.4.0 knots 5_2, 5_2, 6_1: static candidate, NOT certified topological equivalence after bending.
2. Two exact reference datasets from the user (`borromean_flat.txt`, `borromean_balanced.txt`) are not to be swapped, modified or silently planarly projected. The `flat` reference contains nonzero z coordinates.
3. Output XYZ has precisely three blocks with one empty separator and no labels or headers. Direct KnotPlot `load` of the text is the supported import path.
4. Static minimum distances and pairwise Gauss linking pass a threshold. These do **not** show true Borromean structure. Component polynomials, Milnor mu123, and continuous isotopy are `UNRESOLVED`.
5. The source near-unknot central winding is 0, indicating a **material obstruction** to assuming the scaffold's Borromean triple invariant survives a simple carrier transport. If the transported whole curves are degree-zero satellites, the standard triple invariant is not expected to be inherited. Do not silently assume |mu123|=1.
6. `go`/`ago`, force switches, and tanforce remain KnotPlot geometry/dynamics only, not inviscid Euler flows.
7. Numeric coordinates in arbitrary KnotPlot units, global scale 60 fixed across N1024 and N2048. No dependence of scaling on bead resolution.

## Readiness gates

- G0 v0.4.0 manifest source checksums and native seed identity: PASS
- G1 reference raw hash preservation: PASS
- G2 count & syntax of XYZ 3-component block format: PASS
- G3 numerical self and inter-component clearance: PASS at both tested N
- G4 pairwise linking Lk_ij approx 0: PASS
- G5 source knot identity *after* embedding: UNRESOLVED
- G6 continuous isotopy of whole mapping: UNRESOLVED
- G7 Milnor bar(mu)_123 = +/-1: UNRESOLVED
- G8 KnotPlot actual load & three-component count: NOT RUN
- G9 KnotPlot `ago` convergence + after-topology: NOT RUN
- G10 Euler/PKLSA vortex dynamics / toroidal roll: NOT RUN

**Status**: DEVELOPMENT / STATIC_CANDIDATE, not certified Borromean.
