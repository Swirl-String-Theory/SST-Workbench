# Validation

Before a production run, `run_all.cmd` verifies the sealed package, runs unit tests, stages the exact frozen external geometry panel with raw SHA-256 checks, re-runs preflight including staged hashes, and audits blind code/config for source identity and SST-target leakage.

The package contains no primary geometry fallback. Missing or changed external files fail closed.
