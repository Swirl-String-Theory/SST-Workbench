# v0.5.0a (2026-10-22) — deterministic 6_1 closure-facing default

* Borromean placement defaults to `FIXED61`: 180° for every `6_1`; 0° for other knot types.
* Both `5_5_6` and `6_6_5`, all FLAT/SOFT/BALANCED/TIGHT shapes and both mirrored branches covered.
* Original isolated `6_1` seeds and master unchanged.
* Legacy `CENTER`, `LEGACY`, and opt-in `MANUAL` policies remain available.
* All v0.5.0a link geometry / aliases / campaigns regenerated with separate provenance IDs.
* Pairwise linking/clearance gates unchanged; full link topology still unresolved.

# v0.5.0

- Standalone v0.5.0 sibling of the provided patched v0.4.x A006 directory.
- New central bounded-curvature closure regularization and mandatory turn-angle diagnostics. No misleading blanket smoothness certification.
- Rebuilt original + mirror individual twist/torus XYZs from source. Complete fresh link placement for 556 and 665 in all four profiles and four bead resolutions, with strict XYZ three-block export.
- Rebuilt fresh 8k/500 checkpoint campaigns and `go beadlimit` adaptation; TOML/JSON protocol separation from old campaigns.
- Rebuilt all geometry aliases in the supplied RC with new version-specific file targets and `ago 32` aliases.
- Fresh Python release verifier and analysis; no KnotPlot runtime data fabricated.
