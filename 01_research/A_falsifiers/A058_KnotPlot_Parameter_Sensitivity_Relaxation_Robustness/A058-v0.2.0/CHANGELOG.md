# CHANGELOG

## v0.2.0
- Replaced broad multi-topology parameter pilot with single catalogue trefoil.
- Added exact quarter-octave default-relative strength ladder and exact-zero endpoint.
- All non-strength relaxation controls now remain at reset-all defaults.
- Added conditional third-axis design because its force is reset-all-disabled.
- Removed dependency on KnotPlot data CSV logging; coordinates are authoritative.
- Added install integration test that creates and validates exactly one trefoil ASCII export and performs no relaxation.
- Restored canonical Framework-v1.0.6 gate semantics.
