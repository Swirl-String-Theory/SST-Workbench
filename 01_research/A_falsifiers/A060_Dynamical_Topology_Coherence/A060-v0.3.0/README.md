# A060 v0.3.0 — cross-falsifier provenance & name-conflict repair

This is an **additive independent post-run integration layer**, not a rebuild of the A060-v0.2.1 C++/analytic engine. Existing original G0-G5 analytic controls stay unchanged. A060 v0.2.1 G8 currently lists `UNRESOLVED_A045_NAME_CONFLICT`, `A054_state_selection=NOT_IMPORTED`, and `PKLSA_physical_simulation=NOT_RUN`.

Scientific number mapping: A045 = Two-Harmonic Phase-Chirality Floquet; A046 = Relative Vorticity Triadic Geometry. Legacy registry amendments should be performed only after comparing registries, without relabeling any historical sealed evidence.

`run_all.cmd SELFTEST`

Edit `inputs.json` with paths to **machine-readable actual result files** (A045 `CHECK_RESULT.json`, A046 `BLIND_RESULT.json`, A058 actual original run ledger or coordinator output, A054 v0.5.1 machine-readable state result). Empty fields `null` produce NOT_RUN. Then:
```
run_all.cmd FREEZE
run_all.cmd RUN
```

FREEZE seals the identity map, path selection and exact source hashes. Source replacement after FREEZE FAILS CLOSED; a new release/version is required for changes. This is retrospective evidence integration (not prospective blinding); it cannot turn native parity or surrogate benchmarks into a physical gravity/stability conclusion. `OUTPUTS/GATE_LEDGER.json` and `RUN_SUMMARY.json` are generated under unique directory names.
