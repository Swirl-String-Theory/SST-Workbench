# A058 Heavy-32768 Locked RunKit v1.0.1

## Correction from v1.0.0

- Correct false mismatch from Linux/Windows path serialization of `selection_from` in the exact v0.2.10 selector output.
- Compare the three floating-point selection diagnostics with bounded cross-platform tolerances (`rel_tol=1e-9`, `abs_tol=1e-12`).
- Preserve strict ID/order, reasons, source identities, source hashes, other fields, and the original frozen selection JSON / commitment.
- Apply the same comparator to both `CHECK_ONLY` and post-run `VERIFY`.
- Give field-specific error details if an actual discrepancy remains.
- Add ten stdlib regression tests including deliberate decision mutations and source-hash drift.

**Scientific selection unchanged.** No A058-v0.2.10 Python, science contracts, source data, prior BLIND outputs, selection manifest or commitment were edited.
