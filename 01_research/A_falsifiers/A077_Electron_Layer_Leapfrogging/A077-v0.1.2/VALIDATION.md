# A077-v0.1.2 - validation ledger

Scope: G10 post-backend lifecycle correction only; original science kernels and finite-core research pilot remain unchanged.

- Source: generated from the official Framework v1.1.0 generator, with fresh private commitments.
- All 142 original framework runtime source files must match the embedded manifest.
- G10 must remain absent from the GateLedger until the framework `run_auto_matrix` returns; only the framework runner may record G10.
- G10 = PASS only with two genuinely executed, source-hash-validated science backends and numeric parity within the frozen tolerances.
- G10 = UNRESOLVED for missing second backend, malformed tolerance or insufficient reference evidence.
- G10 = FAIL for genuinely measured non-parity; never reclassify numerical failures as physical evidence.
- G3/G4/G8 physical claims remain UNRESOLVED even when G10 qualifies.
- Run project tests, framework tests, and the full pipeline on Windows with actual pybind11.
- No target-machine result is asserted by this release package.
- After execution, inspect `GATE_LEDGER.json`, `AUTO_BACKEND_MATRIX.json`, and each `backend_science/{py,cpp}.json` plus `RUN_SUMMARY.json`, signed output manifest, PDF and BLIND ZIP.
- Do not modify a frozen protocol: make a new version if criteria or physical test change.
