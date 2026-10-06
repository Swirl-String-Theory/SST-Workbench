# Validation

`run_all.cmd` verifies the v0.3.2 seal, stages the exact frozen external geometry panel with raw SHA-256 checks, re-runs preflight including staged hashes, audits blind code/config for source identity and fixed-mode leakage, and runs the complete Python test suite before dynamics.

The package contains no synthetic geometry fallback. Missing or changed external files fail closed.

v0.3.2 also freezes the supplied v0.3.0 parent `blind_results.json` SHA-256 in `provenance/PARENT_V030_RESULT_SNAPSHOT.json`. Parent pressure-memory/spatial/divergence outcomes are contextual evidence only and are not recomputed or allowed to affect the v0.3.2 branch/phase classification.

Required regression controls include stationary phase, monotone chirp, coherent angular-rate reversal, incoherent random phase, and branch retention when the inherited v0.3.0 stationary persistence flag is false.
