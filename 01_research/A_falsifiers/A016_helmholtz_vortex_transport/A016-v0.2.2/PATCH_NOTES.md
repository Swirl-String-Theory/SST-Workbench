# A016 v0.2.1 -> v0.2.2 patch notes

Do **not** modify the frozen v0.2.1 directory in place. Install `A016-v0.2.2` as a sibling version under the same A016 family.

v0.2.2 replaces the unrealized E010-v0.4.0 publication-ready source contract with the existing Workbench chain:

```text
E010-v0.3.1 qualification
        -> E011-v0.3.0 STATIC_READY atlas
        -> A016-v0.2.2
```

Automatic mode selection:

- `BASIC`: stratified subset of E011 provider anchors (maximum 8 carriers).
- `FULL`: all E011 `STATIC_READY_PROVIDER_ANCHORS.jsonl` records.
- `CERTIFY`: all E011 `STATIC_READY_PRIMARY_SEEDS.jsonl` records plus strict B0 backend certification.

The preflight accepts the E011 admitted subset even when E010's global release reports `publication_ready_geometry_layer=false`; it still requires E011 execution PASS, zero operational errors, E010 parent version 0.3.1, the E010 source/topology/identity gates, exact raw-source hashes, and supported source-native representations.

Run from `A016-v0.2.2`:

```bat
run_all.cmd SELFTEST
run_all.cmd BASIC
run_all.cmd FULL
run_all.cmd CERTIFY
```
