# v0.4.0 -> v0.4.1 migration

## Scientific invariants

Unchanged: research question, E1--E6, decision thresholds, A054 source campaign identity, v0.3.1 discovery source, spatial ladder, Jacobian epsilon values, CPU parity tolerance and blind semantic boundary.

## Execution changes

1. Canonical framework pin moves from v1.0.4 to v1.0.6.
2. The upstream isolated runner is staged from the manifest allowlist before import.
3. Unlisted native extensions are excluded from the staged namespace.
4. Exact-SHA native-source restoration is permitted only to reproduce the manifest-listed bytes; no alternate rebuild is accepted.
5. G5 is independent of G2.
6. G8 depends on G2+G5 and remains evaluable when G3 is a clean FAIL.
7. Diagnostic continuation is stored separately from the authoritative gate ledger.
8. Reveal requires terminal G8 and v1.0.6 blind-output integrity verification.
