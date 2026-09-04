# Changelog

## v0.1.2 — metadata-integrity / geometry-gate hardening

- **Critical:** honors generator `geometry_ok=false`; rejected QHP geometries are excluded before blind preparation and physics.
- Hard-fails duplicate geometry file paths in `qhp_metadata.csv`.
- Hard-fails duplicate `(family, replicate, q, h, p)` manifold nodes, which would make finite differences ambiguous.
- `prepare_summary.json` now records total metadata rows and the number excluded by the geometry gate.
- Compatible with QHP Sweep Generator v0.1.1 unique seed identities (`knot_6.3`, `link_6.3.1`, etc.).
- No changes to Biot--Savart physics, QHP projection equations, fixed-point criterion, or stability thresholds.
