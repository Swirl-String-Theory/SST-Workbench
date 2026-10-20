# A003 Fourier Knot Import Adapter v0.2.6 — 2026-10-19

Parent release: **v0.2.5**. Atlas input remains pinned to A003-v0.1.2, manifest SHA-256 `01d57ec3f259fee4a09caa6aac8d3410ad6e1d8a8f159c6a9fb7ba71d0a6169d`.

- Added external **SST Falsifier Framework v1.0.10 GateLedger** binding with strict API, version and source SHA-256 checks; release remains `LOCAL_VALIDATED_CANDIDATE`.
- Added v1.0.10 `run_evaluators` non-short-circuit execution: measured G5 FAIL does not prevent G5e and G5f diagnostics; recursive qualification remains `DIAGNOSTIC_ONLY` on blocked downstream claims.
- Added `crossing_trace.py`: exact polygon projected crossing enumeration, over/under Gauss events, integer Wirtinger/Fox determinant at t=-1; writes immutable per-case JSON.
- Added G5f independent diagram vs pyknotid determinant comparison, replaying N=2400 P1 provider 1 vs independent 3.
- Added `run_g5_diagnostic.cmd`, `run_g5_diagnostic_replay.cmd`, `run_g5_diagnostic_smoke.cmd`, `run_all.cmd DIAGNOSTIC`.
- Added unique per-run output identity; GATE_LEDGER.json, separate diagnostic summary, .md/.tex and optional auto-built PDF.
- Added `tests/fixtures/g5_v025_extended_replay.json` from user-supplied v0.2.5 source; replay labeled historical, never a new measurement.
- Added seven regression tests (58/58 PASS with genuine framework GateLedger source fixture). Existing G0–G4 thresholds and G5a-d primary projection angles unchanged, v0.2.5 scientific FAIL retained.
- G6/PKLSA/Euler and G9 reveal remain NOT_RUN. No independent knot/chirality certification.
