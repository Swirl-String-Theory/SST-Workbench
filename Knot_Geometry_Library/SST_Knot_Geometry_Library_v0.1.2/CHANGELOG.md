# Changelog

## v0.1.2 — 2026-08-29

- Fixed Windows CRLF portability of the blind reveal commitment. `reveal.json` is now written as canonical UTF-8 bytes with LF newlines, and the commitment hashes the exact bytes written to disk.
- Added `verify_blind_campaign()` and CLI command `verify-campaign` to audit all anonymous geometry hashes, manifest/reveal consistency, and the exact reveal commitment.
- `run_all.cmd` now writes `outputs\blind_campaign_verification.json` and fails if the blind campaign cannot be verified.
- Geometry formulas, native numerical kernels, qualification thresholds, and candidate parameter grids are unchanged.

## v0.1.1 — 2026-08-29

- Fixed MSVC/Windows native build failure caused by POSIX-only unqualified `ssize_t` in `cpp/native.cpp`.
- Replaced the loop/index storage with portable `std::size_t` and an explicit `<cstddef>` include.
- Added an explicit native-extension import/OpenMP check to `run_all.cmd`; full validation now fails if the compiled backend cannot be imported.
- No geometry formulas, blind-campaign semantics, qualification gates, or numerical kernels were changed.

## v0.1.0 — 2026-08-29

- Added independent trigonometric trefoil constructor.
- Added general anisotropic `torus_knot(p,q,R,a,b)` constructor.
- Added shader-track-derived `track_trefoil` family with independent radial bulge and axial weave.
- Added figure-eight `S3 -> SO(4) -> stereographic` control with projection-pole guard.
- Added uniform arclength resampling and periodic Fourier smoothing.
- Added discrete Bishop/rotation-minimizing frames.
- Added material thread bundles and ribbon edges.
- Added C++17/pybind11 kernels for segment clearance, writhe and linking.
- Added `Lk/Wr/Tw` self-linking report.
- Added geometry qualification and resolution convergence gates.
- Added blind campaign generation with SHA-256 reveal commitment.
- Added Windows `run_all.cmd`, `run_basic.cmd`, and `run_campaign.cmd`.
- Added integration notes for current SST seed/stability/threaded-hole/finite-core falsifiers.
