# Validation

Before a v0.3.1 run, `run_all.cmd` verifies the v0.3.1 seal, runs unit tests, stages the exact frozen v0.3.0 external geometry panel with raw SHA-256 checks, re-runs preflight including staged hashes, and audits blind code/config for source identity and SST-target leakage.

The new phase/frequency classifier is tested against deterministic stationary, chirped, and random-phase synthetic series. The diagnostic is explicitly excluded from the parent v0.3.0 acceptance logic.

The package contains no primary geometry fallback. Missing or changed external files fail closed.
