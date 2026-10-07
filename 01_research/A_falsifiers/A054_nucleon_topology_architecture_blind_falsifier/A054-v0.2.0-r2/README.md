# A054 v0.2.0-r2 provenance repair v0.1.0

This repair is specific to the mixed anonymous-ID campaign state observed in:

`A054_Nucleon_Topology_Architecture_Blind_Falsifier_v0.2.0-outputs/full_20261006_230912`

## What it repairs

The completed scientific outputs were sealed against one anonymous candidate namespace,
but a later prepare/run overwrote `BLIND_MANIFEST.json` and `_private/PRIVATE_MAPPING.json`
with a second 72-candidate anonymous namespace.

The numerical campaign itself is complete:

- 72 candidates
- 4 circulation sectors
- N = 56, 72, 88
- 864 numerical candidate/sector/resolution cells
- 288 sector summary rows
- 1152 total result rows

The repair does **not** recompute or modify:

- `CERT_RESULTS_BLIND.json`
- `CERT_ANALYSIS_BLIND.json`
- `CERT_REPORT_BLIND.md`
- `CERT_CONFIG.json`
- `BACKEND_QUALIFICATION.json`

## Repair method

For each of the 72 anonymous IDs occurring in `CERT_RESULTS_BLIND.json`, the script:

1. requires the preserved `blind_inputs/<anonymous_id>.npz`;
2. computes its exact SHA-256;
3. matches it to exactly one candidate in the current manifest;
4. transfers the corresponding private semantic mapping to the result ID;
5. requires a 72/72 bijection with no collisions;
6. rebuilds manifest/private mapping for the IDs actually used by the results;
7. writes an explicit repaired seal.

No fuzzy geometry matching is used. Matching is byte-exact SHA-256.

## Audit trail

Before replacement, the script backs up:

- original/mixed `BLIND_MANIFEST.json`
- original/mixed `_private/PRIVATE_MAPPING.json`
- historical `CERT_BLIND_SEAL.json`

under:

`_provenance_repair_backup/`

It also creates:

- `PROVENANCE_REPAIR_BIJECTION_BLIND.json`
- `PROVENANCE_REPAIR_REPORT.json`
- `PROVENANCE_REPAIR_STATUS.json`

The new seal schema is:

`A054-CERT-BLIND-SEAL-2.0-REPAIRED`

This makes the repair explicit rather than pretending the repaired seal is the historical
pre-overwrite seal.

## Apply to your local A054-v0.2.0-r2

Copy these three files into the A054-v0.2.0-r2 root:

- `repair_a054_r2_provenance.py`
- `apply_provenance_repair.cmd`
- `verify_provenance_repair.cmd`

Then run:

```bat
apply_provenance_repair.cmd
verify_provenance_repair.cmd
```

Expected verification:

```text
"status": "PASS"
"seal_mismatches": {}
"result_ids": 72
"manifest_ids": 72
"private_ids": 72
"namespace_equal": true
```

## A055 v0.3.0 compatibility

The repaired campaign was tested directly with the A055 v0.3.0
`verify_a054_seal()` and `derive_blind_compound_features()` routines:

- A055 seal verification: PASS
- compound candidates: 72
- compound sector rows: 288
- fine resolution: 88

After the repair you may restart:

```bat
run_all.cmd full
```

from A055-v0.3.0. It should discover the repaired completed A054 full campaign instead of
starting another A054 full run.

## Scientific boundary

This is a provenance/namespace repair only. It does not alter any physical result, gate,
eigenvalue, ringdown result, RPO result, Floquet result, configuration, or backend
qualification.
