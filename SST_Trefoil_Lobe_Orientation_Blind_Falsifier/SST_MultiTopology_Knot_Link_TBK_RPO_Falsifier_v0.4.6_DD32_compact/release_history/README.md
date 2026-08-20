# Compact scientific release history

Starting with v0.4.5.3, release history is intentionally compact. The old ZIP-in-ZIP policy caused exponential package growth without adding scientific information.

## Embedded scientific capsule

Only `SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.1.zip` is embedded. It is the last pre-runtime-maintenance scientific archive release and already contains the exact v0.1.0, v0.1.1, v0.2.0, v0.3.0 and v0.4.0 ZIP chain internally. Its byte hash is in `INDEX.sha256`.

## Omitted runtime-only releases

v0.4.2 through v0.4.5.2 were runtime/Windows/SYCL/UX maintenance releases. They changed no preregistered scientific gates, thresholds, archive inventory, perturbation basis, RPO/Floquet semantics, or confirmatory precision policy. Their original ZIP SHA-256 values are retained in `HISTORICAL_HASHES.sha256`, and their changes remain documented in the top-level `CHANGELOG.md`.

This policy preserves scientific reproducibility while preventing recursive archive bloat.

## Runtime maintenance after v0.4.1

Runtime-only releases v0.4.2 through v0.4.5.4 are tracked by changelog and SHA-256 rather than recursively embedding every ZIP.  The exact v0.4.1 scientific capsule remains embedded and contains the exact v0.1.0–v0.4.0 scientific chain.
