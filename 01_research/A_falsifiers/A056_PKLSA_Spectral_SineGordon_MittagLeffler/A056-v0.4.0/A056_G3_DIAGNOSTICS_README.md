# A056-v0.4.0 read-only G3 diagnostics

This overlay adds a **non-authoritative, read-only** diagnostic for the frozen A056-v0.4.0 Gate 3 model competition.

It does **not** change any preregistered equation, threshold, provider configuration, gate definition, reveal policy, or frozen protocol file. The canonical v0.4.0 G3 result remains unchanged.

Run from the A056-v0.4.0 instance root:

```bat
run_diagnose_g3.cmd
```

Optional alternate provider input directory:

```bat
run_diagnose_g3.cmd data\some_other_runtime
```

Outputs:

- `A056_G3_DIAGNOSTICS_READONLY.json` — complete per-case competitor metrics;
- `A056_G3_DIAGNOSTICS_READONLY.csv` — compact comparison table.

The JSON reports all frozen discovery-model RSS/BIC/coefficient/condition quantities for Wave, Klein-Gordon, Duffing and Sine-Gordon, plus EXP/STRETCHED/BIEXP/Mittag-Leffler ringdown fits. It reconstructs the frozen G3 pass booleans exactly from the unchanged v0.4.0 configuration.

The underlying fitting functions also compute holdout NRMSE values. These are exposed only under explicit `posthoc_*` names. If the canonical run stopped at G3, those values **must not be promoted to G4 evidence**; G4 remains `NOT_RUN_PREREQUISITE`.

No source/carrier reveal information is read or emitted; cases remain identified by `opaque_id`.
