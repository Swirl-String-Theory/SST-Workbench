# PKLSA integration contract — A043 v0.2.0

## Scope

v0.2.0 consumes only the PKLSA `knot_3.1` branch as an SST trefoil population. The signed atlas contract is 48 variants, one component, 512 points/component, bundle `families/14_knot_3p1.npz`.

The 48 cases are **not 48 independent source replications**. They are a dependency-aware shape population derived from PTSA v1.0.0 and preserved by PKLSA up to global similarity normalization.

## Fail-closed ingest

Before dynamics, the adapter requires:

1. exactly 48 manifest rows with variant indices 0..47;
2. `family=knot_3.1`, `canonical_id=3_1`, `family_index=14`;
3. one component and 512 points/component;
4. the expected construction method;
5. finite `points` with array shape `(48,1,512,3)`;
6. for scientific BASIC/certification runs, SHA-256 `ffc31331fccaf10a3171e4ccbf3ec0043e56ff681f85cc8b8149932193d736d1`.

`pklsa_smoke.json` can disable only item 6 so a generated schema fixture can exercise the software path. Smoke output is not scientific evidence.

## Common canonicalization

Each centerline is transformed by

- periodic closed-curve arclength resampling;
- centroid removal;
- one uniform scale to a preregistered RMS radius;
- no rotation and no reflection.

Thus shape differences are retained while translation and absolute source scale do not affect the Euler initialization.

## Blindness

Candidate IDs, PTSA IDs, parameter triples and variant indices are reveal-only. BLIND uses fresh salted anonymous geometry and case IDs. A candidate may escalate only if **that same anonymous geometry** produces a compatible BKM candidate on at least three distinct spatial resolutions.
