# Changelog

## v0.2.1 — Native Knot_Library provenance layout

### Added
- `Knot_Library/` provenance roots: `Sources/`, `Registry/`, `Derived/`, `Quarantine/`.
- Machine provider IDs via `Registry/providers.json` + per-provider `SOURCE.json` (`sst-knot-library-source/1`).
- `library_root.py`: discover `Knot_Library`, resolve `provider_id` / `provider_class` without parsing directory names as identity.
- `inventory-sources` CLI: classify legacy Workbench paths into Registry JSON; never moves files.
- GeometryAsset / KnotRecord fields: `provider_id`, `provider_name`, `provider_class`.
- `scan-dataset` defaults to `Knot_Library/Sources` when no root is passed.
- Strict entry policy requires a known `provider_id` (unknown provenance → Quarantine, not strict falsifier input).

### Changed
- Path heuristics (`ideal_txt`, `knotplot_fseries`, …) are fallbacks only outside Sources; under Sources the SOURCE.json provider wins.
- Docs/examples no longer point at `KnotPlot/knots/final` as the canonical dataset root.

### Preserved
- v0.2.0 geometry/topology API and smoke-test behaviour for paths outside Sources.

## v0.2.0 — SST Knot Library umbrella release

### Added
- Offline SHA-256 verified KAtlas snapshot for `3_1`, `4_1`, `6_2`, `7_4`.
- Explicit topology status model: CERTIFIED / MISMATCH / UNVERIFIED / NOT_REGISTERED / ERROR.
- Optional provider discovery for pyknotid, Spherogram, SnapPy, KnotPlot and Ridgerunner.
- Optional pyknotid space-curve certification adapter.
- Optional Spherogram/SnapPy reference cross-checks.
- Generic Artin braid closure geometry generator and KAtlas-braid seeds.
- `7_4` Lissajous independent seed.
- Multi-component VECT reader/writer.
- KnotPlot 1.0 LOCD/LOCF binary reader; quantized LOCS/LOCC reject-by-default safety policy.
- Unified `load_geometry`, `make_knot_record`, dataset scanner and falsifier entry policies.
- `inspect`, `scan-dataset`, `registry`, `providers`, `crosscheck-reference`, `braid-info`, and `seed-from-topology` CLI commands.
- Source-byte hashes, canonical geometry hashes and registry provenance in knot records.

### Preserved
- v0.1.3 geometry API under `sst_knotlib`.
- C++17/OpenMP native geometry kernels.
- byte-exact blind campaign commitments.

### Policy change
A topology inferred from a filename is never considered certified. This is intentional and may expose previous datasets as `UNVERIFIED` until an independent topology provider is run.
