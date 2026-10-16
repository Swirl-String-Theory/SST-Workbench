# A058 changelog

## v0.2.9 — finite-time matched-budget campaign, Framework v1.0.8

- `run_all.cmd BASIC` / `512` runs all 271 conditions to 512 go iterations with checkpoints 32/128/512.
- `run_all.cmd 2048` runs all 271 conditions at 32/128/512/2048.
- `run_all.cmd 32768` runs a blinded, automatically selected subset (at most 31) at 32/128/512/2048/8192/32768, based solely on a completed earlier tier.
- Disallows treating fixed-budget endpoint as adaptive convergence; updates science/falsification/report contracts.
- New non-overwriting `campaign/runs/<tier>/` acquisition ledger and deterministic heavy selection with source hashes.
- Short sector-specific preflights; explicit GUI-start fallback for historical freeglut drag failure, without hiding unsupported lanes.
- Avoids 180-second polling when the KnotPlot process exits or reports fatal freeglut errors.
- Preserves v0.2.8 shared safe seed prep, Damped/collision, S3 default 1.40 in R2 sector and eight GUI controls.
- Framework v1.0.8 retained, new version gets new private key, nonce and preregistration commitments.

## v0.2.8

Previous version preserved separately. Historical source/provenance available in v0.2.8 ZIP.
