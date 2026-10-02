# Validation — SST Trefoil Dynamic Seed Qualification Mega Falsifier v0.3.1

Date: 2026-09-03

## Scope

v0.3.1 changes Python workflow/diagnostic code only.  `cpp/native.cpp` is unchanged from
v0.3.0, whose native Windows CPython 3.14/OpenMP backend was validated by the user's
v0.3.0 campaign.  This Linux container does not contain the `pybind11` Python package, so
the Windows extension was not rebuilt here; `run_01_build_native.cmd` remains the decisive
MSVC validation on the user's machine.

## Automated tests in this environment

- pytest: **61 PASS, 1 SKIP**.
- Python fallback self-test: PASS.
- `compile` / module import checks for the new S37B, post-hoc and archive modules: PASS.

The skipped test is an existing optional native/backend-specific test in this environment,
not an S37B logic failure.

## New v0.3.1 tests

The suite explicitly verifies:

- `segment_feedback` adds tangent-only mesh velocity;
- `target_projection` adds tangent-only mesh velocity;
- `mesh_off` adds exactly zero mesh velocity;
- all S37B arms at one resolution use the identical frozen `(steps, dt, guard_stride)`;
- raw-label displacement decomposition and arclength-invariant shape distance are finite;
- S37B operates on the S35-qualified set even when S37A has zero qualifiers;
- every S37B classification has `promotion_to_s40_allowed = false`;
- one-click scripts include S37A followed by S37B;
- blind archive construction excludes `*_sealed_private` and blind-key material;
- release identity reports v0.3.1.

## End-to-end workflow smoke

A three-family synthetic trefoil workflow was executed with deliberately tiny horizons and
Python fallback to validate stage plumbing only.  The chain completed
`S20 -> S30 -> S32 -> S35 -> S37A -> S37B -> S40 -> S50 -> S60`.
S37B produced one diagnostic row per tested candidate and the summary explicitly retained
`promotion_to_s40_allowed = false`.  This run is software validation, not physics evidence.

## Historical v0.3.0 post-hoc smoke

The supplied v0.3.0 public campaign was used for a **software-only** post-hoc S37B smoke
run at a deliberately tiny validation resolution/time with Python fallback.  The diagnostic
successfully:

- found the four S35-qualified anonymous candidates;
- independently re-hashed all four `.npy` geometries against the old public manifest;
- recorded SHA-256 attestations for the old public S35/S37/evidence files;
- produced four diagnostic rows without reading the sealed identity bundle.

This smoke test is not physics evidence and is not reported as a mesh-closure result.

## Hash semantics

v0.3.1 makes the two commitment semantics explicit:

- binary secrets: `raw_bytes_sha256_v1`;
- JSON object commitments: `canonical_json_sorted_compact_ascii_v1`.

This removes the audit ambiguity observed when pretty-printed JSON bytes were compared
against canonical-object commitments in v0.3.0.

## Scientific non-claims

S37A thresholds are unchanged.  S37B cannot promote to S40 and cannot turn an old
`INDETERMINATE` result into a pass.  No new RPO, Floquet or causal-mechanism claim is made
by the release validation itself.
