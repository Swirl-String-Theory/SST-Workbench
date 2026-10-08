# A056-v0.3.0 E010 / PKLSA dynamic-provider integration

Runtime authority is the live E010-v0.3.1 production result, in this order: `RELEASE.json`; `poc/atlas/3_1/qualification/summary.json`; `source_independence.json`; `geometry_metrics.json`; carrier envelopes; original source bytes. A056 uses the E010 loaders and recomputes raw SHA-256 plus `PKLSA-GEOMETRY-SHA256-v1` before any dynamics.

The default real-provider selection is deliberately narrow: carriers must pass the E010 literature hard gates, be geometry/raw unique, not be mirror evidence, and have `contributes_new_upstream_provider=true`. The current production ledger is expected to yield at least two provider groups, but the count and carrier IDs are not hard-coded.

A056 does **not** inherit a physical conclusion from E010 or A047. E010 supplies qualified source-native geometry/provenance. The A047 v0.3.0 finite-width Euler construction is the method provenance for the volumetric provider. A056 independently creates its own paired perturbation observable and performs its own SG/ML scoring.

Different grid/marker resolutions of one carrier are convergence replays. They are grouped by an opaque `provider_case_family` and never counted as independent replication.
