# CHANGELOG

## v0.3.8 — 2026-10-23

- Added `tools/scalar_export_closure.py` with `AUDIT_SCALAR_CLOSURE`, `GENERATE_SCALAR_CLOSURE`, `RUN_SCALAR_CLOSURE` modes.
- Bound the 2026 native 4-case data-initialization experiment by hashes: two good-before cases and two bad-after controls; the failure cases remain failed.
- Registered a **separate non-blind** 2 x 3 matrix for dstep 1/4 and go 32/128/512, each in a separate native process and each with independent XYZ/CSV comparison.
- Exact qualified order preserved: completed `go` followed by `data open; data format; data header; length; rog; data; data close`.
- Added before/after `parameters` readback and explicit verification of `iteration` and velocity/tangent/gravity/thermal flags.
- Added dual read-only historical and new native report schemas, SHA-256 source hashes, non-overwriting run directories and tests.
- Old A058 271-condition preregistration and Framework pin left unchanged. No physical claim.

## v0.3.7 and earlier

Refer to the preserved v0.3.7 README and REPAIR_NOTES for earlier releases.
