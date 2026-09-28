# Changelog

## v0.3.0

- Added falsifier-facing `STATIC_READY` seed certification.
- Added provider-agreement gates and empirical uncertainty envelopes.
- Added per-observable capability flags rather than forcing all static observables to converge for all seed uses.
- Added source metadata extraction from E010 for frozen carrier/hash/provenance locators.
- Added primary, secondary and control seedsets; mirrors are never STATIC_READY.
- Added topology statuses distinguishing cross-provider robust/sensitive/incomplete and single-provider evidence.
- Added `SEED_CONTRACT_SCHEMA.json` for downstream SST falsifiers.
- Retained carrier-level E010 literature admission and auditability from v0.2.0.
- No physical best-seed score and no DYNAMICS_READY claim.
