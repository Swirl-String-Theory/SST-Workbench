# Changelog

## v0.2.2 — topology namespace + Gilbert Fourier trust hotfix

### Fixed
- Added disjoint knot/link/torus topology namespaces so `link_6.2.1` is no longer mislabeled as knot `6_2`, and `torus_3.6` is no longer mislabeled as knot `3_6`.
- Added `infer_topology_hint_from_name()`; legacy `infer_knot_id_from_name()` is now knot-only.
- Added a release-identity attestation gate. `run_all.cmd` fails when `RELEASE.json` and runtime `__version__` disagree.
- Runtime attestation again embeds the complete provider status plus source-catalog identity.

### Added
- Brian Gilbert / Knot Atlas Ideal-Knots Fourier decoder for `<AB>/<HT>` records using the documented `A[i], B[i]` series.
- Source-provider catalog with SHA-256 verification.
- Known metadata-file classification; `0TwelveData.csv` is `SKIPPED_METADATA`, not a geometry parse error.
- Component-count consistency checks between link/torus filename hints and loaded geometry.
- `sources` CLI report.
- Audit of the submitted v0.2.0-labelled Windows output set.

### Preserved
- Geometry kernels, blind-campaign hashing, KAtlas snapshot, braid constructors and qualification equations are unchanged from the v0.2.x umbrella line.

## v0.2.0 — SST Knot Library umbrella release

- Offline SHA-256 verified KAtlas snapshot for `3_1`, `4_1`, `6_2`, `7_4`.
- Explicit topology status model and optional topology providers.
- Generic Artin braid closures, VECT and KnotPlot LOCD/LOCF import, geometry records, policies and dataset scanning.
