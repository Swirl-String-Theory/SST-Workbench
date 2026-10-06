# Validation

`run_all.cmd` performs the following fail-closed sequence:

1. verify the v0.4.0 code/config seal and frozen v0.3.2 evidence snapshot;
2. stage the original external baselines through the existing provenance-qualified v0.3.2 route;
3. generate a fresh deterministic v0.4.0 holdout panel and hash every generated carrier;
4. verify both source and fresh manifests;
5. audit blind code/config for SST constants, source identity, topology/provider labels, and hard-coded mode-3 targets;
6. run unit tests including synthetic beating, chirp, phase-slip, RPO-positive, and recurrence-negative controls;
7. run the blind mechanism campaign and hash `blind_results.json`.

Missing or changed geometry files fail closed. Floquet/monodromy remains inactive even if `RPO_CANDIDATE` is observed.
