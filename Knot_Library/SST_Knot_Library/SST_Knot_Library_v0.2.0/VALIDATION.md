# Validation v0.2.0

Validated in the build environment before packaging:

- Python smoke suite: **15/15 PASS**.
- Standalone C++17/OpenMP kernel: **PASS**.
- KAtlas snapshot SHA-256 validation: **PASS**.
- Core snapshot IDs: `3_1`, `4_1`, `6_2`, `7_4`.
- Braid closure component count matches KAtlas component count for all four core records.
- Generic braid seeds generated finite, closed-resampled coordinate sets for all four records.
- Multi-component VECT round-trip: **PASS**.
- Synthetic KnotPlot 1.0 network-order LOCD binary round-trip: **PASS**.
- S3 inverse/projective round-trip: **PASS**.
- trefoil ribbon self-linking integer residual gate: **PASS**.
- byte-exact blind reveal commitment test: **PASS**.
- `reference-only` topology mode verified to remain `UNVERIFIED`, never false-CERTIFIED.

`run_all.cmd` on Windows additionally requires successful pybind11 native import and OpenMP before it reports PASS. Optional third-party topology providers are reported but are not required by core validation.

The generated braid closure geometry is a topology-controlled seed family, not an ideal-knot or Euler-stability claim. Publication-grade geometry identity should be cross-checked with an independent space-curve provider under `strict` policy.
