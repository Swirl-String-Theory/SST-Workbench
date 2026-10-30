# B007 v0.2.1 - Validation / release scope

- Version: v0.2.1, derived from unchanged v0.2.0 reference source and vendored E010 v0.3.6 analytic generator.
- Custom imported link curves: four families, 6 raw XYZ/TXT files plus four original JSON sidecars; all bytes included and SHA-256 recorded.
- Three components are parsed from blank-line separated blocks and are not stitched.
- Both 1024 and 2048 original source discretizations of the two composite-link families can be selected independently.
- Approximate pairwise Gauss linking near zero does not certify Borromean isotopy; Milnor mu123 unresolved.
- Generated higher vertex counts are arclength interpolants of the source polygon, not independent physical data or analytic curve seeds.
- Circulation modes: equal total signed circulation (default) and equal per-component circulation; no unfair direct cross-mode ranking.
- All four imported families tested end-to-end through G1-G3. G4 without extra background returned BLOCKED_SPECTRAL_UNDERRESOLUTION; G4 with one fully live background loop returned BLOCKED_GEOMETRIC_SEPARATION.
- Analytic T_2_3 legacy path tested, import provenance and parameter selection regression tested.
- Source/outputs release SHA-256 manifests and ZIP testzip checked at packaging.
- Scientific status: G2_UNRESOLVED_NO_CERTIFIED_EQUILIBRIUM. No nonlinear relative equilibrium, Milnor invariant, physical stability, or finite-core convergence certified.
