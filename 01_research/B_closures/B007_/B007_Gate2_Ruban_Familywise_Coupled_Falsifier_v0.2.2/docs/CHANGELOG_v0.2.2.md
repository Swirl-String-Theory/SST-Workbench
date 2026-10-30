# B007 v0.2.2 — Scientific and engineering changes

Status: DEVELOPMENT; nothing here certifies Borromean isotopy, Euler equilibrium or long-time stability.

## Main scientific fix

- Introduced free rigid-velocity least-squares fit with U=(Ux,Uy,Uz) and Omega=(Ox,Oy,Oz), centered at an arclength-weighted position.
- Retained fixed-axis two-parameter U_z and Omega_z comparator. `--fit-mode compare` selects by **free** fit while exporting both diagnostics.
- Arclength weighting is default, ensuring samples represent curve length, not mere point count. `--fit-mode axial --fit-weighting vertex` permits regression comparison with legacy v0.2.1.
- The residual fit only projects *instantaneous* velocity. It does not satisfy full-field Euler equilibrium or prove stability. Rotational rigid motion is NOT imposed on the cubic periodic G4 solver.

## Imported source qualification

- Preserves exact imported bytes and verified SHA-256 per file.
- Records original component point counts, per-component polygon lengths, closure-edge ratios, edge spread, center/scale, approximate Gauss pairwise linking at N=128/256, and sampled intercomponent clearance.
- For families with **two genuine supplied source files**, records differences between original 2048-stage and reference 1024-stage polylines. For sparse flat/balanced files, explicitly reports no independent higher-resolution source.
- No certified Milnor μ123, full link isotopy, nonintersection of smooth tubes, or segmentwise Euler evolution.

## Selection / robustness

- G2/G3 preserve both nominal and perturbed curves, real short-time Heun evolution and refinement; all selected scores tagged as provisional.
- Imported links with no spatially eligible pair now have an explicit `PROVISIONAL_IMPORTED_SPATIALLY_UNRESOLVED_ISOTOPY_UNRESOLVED` state.
- Two physically inequivalent circulation options remain `total` and `per-component`; no silent merging of their rankings.

## Regression evidence

- 41 pytest tests including free SE(3) velocity reconstruction, change-of-orientation invariance, exact axial-legacy regression, fit monotonicity and imported hash/geometry audit.
- Full end-to-end development smoke campaigns run for all four BORRO families, the external-reference axial legacy path, T(3,9) and one coupled G4 live-background pilot.
- Full convergence, broad fine scans, optimized link orientations, Milnor certification, independent native GPU/CPU parity, and G4 solution of stationary Euler are **not** performed.
