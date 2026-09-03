# Validation v0.2.2

Validated in the build environment before packaging:

- Python smoke suite: **20/20 PASS**.
- Standalone C++17/OpenMP kernel: **PASS**.
- KAtlas snapshot SHA-256: PASS.
- Source-provider catalog SHA-256: PASS.
- Brian Gilbert Fourier synthetic reference: PASS.
- Knot/link/torus namespace non-collision tests: PASS.
- Torus component-count rule `gcd(p,q)`: PASS.
- Multi-component VECT round-trip: PASS.
- Synthetic KnotPlot network-order LOCD round-trip: PASS.
- S3 inverse/projective round-trip: PASS.
- trefoil ribbon self-linking integer residual gate: PASS.
- byte-exact blind reveal commitment: PASS.
- release-version identity: PASS in source/editable validation.
- TwelveData summary CSV metadata classification: PASS.

`run_all.cmd` on Windows additionally requires successful pybind11 native import, OpenMP, release
identity and release-file SHA-256 integrity before reporting PASS.
