# Changelog

## v0.4.1

- Migrated the instance pin and launch/bootstrap path to SST Falsifier Framework v1.0.6.
- Added a frozen implementation manifest commitment, verified by G0 before any science gate can close.
- Kept all v0.4.0 science equations, thresholds, A054/A055 upstream source identities and numerical control values unchanged.
- Replaced direct A054 runner import with an exact-manifest import mirror. Unlisted native binaries are excluded; upstream files are never modified.
- Added exact-source recovery for a missing/altered manifest-listed native file, accepted only when SHA-256 equals the frozen runner-manifest value.
- Decoupled G5 local C++ parity from G2 so that a reference/upstream failure does not suppress an independently computable backend diagnostic.
- Changed G8 prerequisites to G2+G5; G3 FAIL no longer short-circuits the recurrence gate.
- Added `A055_DIAGNOSTIC_LEDGER.json` for non-authoritative continuation evidence.
- Tightened reveal policy to require terminal G8 PASS/FAIL and no unresolved blind gates.
- Updated report path wrapping and framework/provenance description.
