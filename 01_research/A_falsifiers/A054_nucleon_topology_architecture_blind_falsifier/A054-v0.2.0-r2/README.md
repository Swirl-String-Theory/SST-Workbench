# A054 v0.2.0-r2 native runner restore

This kit restores **only** the isolated native runner binary for the completed campaign:

`A054_Nucleon_Topology_Architecture_Blind_Falsifier_v0.2.0-outputs/full_20261006_230912`

It does **not** modify the A054 scientific results, analysis, report, config, repaired seal, blind manifest, or private mapping.

## Why

The campaign's `RUNNER_MANIFEST.json` records the canonical native binary SHA-256:

`ba6f8c9fdbcaa2525a4268d597c697c9067a331a170bd63a04b4440d640b2645`

A later local state reported a different binary hash:

`5dccff7e07b66e7a958e1d4f4cd8772f52fc03e188e0dab9e1f2d227dab93f5b`

A055 v0.4.0 correctly refuses to use a runner whose binary no longer matches its own runner manifest.

The payload in this kit is taken from the previously preserved/repaired A054 output snapshot and its SHA-256 is verified before replacement.

## Apply

Copy this kit into the `A054-v0.2.0-r2` root, then run:

```bat
restore_a054_native.cmd
verify_a054_native.cmd
```

The script:

1. verifies the repair payload hash;
2. verifies all manifest-tracked Python source files (runtime `__pycache__` is excluded);
3. backs up the current `_native.pyd` outside the campaign tree;
4. restores the canonical `_native.pyd`;
5. verifies the complete runner source/native manifest again.

Expected final status: `PASS` and native SHA-256 `ba6f8c...b2645`.

Then rerun A055.
