# A016 — Helmholtz Vorticity-Population / Matter–Field Partition Falsifier v0.2.2

Framework target: **SST Falsifier Framework v1.0.6 (CANONICAL_FROZEN)**.

v0.2.2 corrects the external-geometry handoff. The frozen v0.2.1 protocol expected a non-existent E010-v0.4.0 publication-ready atlas and therefore stopped at G1. The real Workbench chain is:

```text
E009 PTSA-v1.0.0 (generated trefoil controls)
          ↓
E010 PKLSA-v0.3.1 (geometry/source/topology qualification)
          ↓
E011 SKLSA-v0.3.0 (falsifier-facing STATIC_READY atlas)
          ↓
A016-v0.2.2
```

A016 now consumes E011-v0.3.0, while preserving every H0–H4/P0–P6/X0 threshold from v0.2.1.

## Admission contract

G1 passes only when the canonical E011-v0.3.0 output bundle contains:

- `RUN_SUMMARY.json` with schema `E011-SKLSA-STATIC-READY-ATLAS-1`, `execution_gate=PASS`, `operational_error_count=0`, and E010 parent version `0.3.1`;
- `SEED_CONTRACT_SCHEMA.json` with schema `E011-STATIC-SEED-CONTRACT-1`, atlas version `0.3.0`, and `dynamics_ready=false`;
- `PARENT_RELEASE.json` identifying E010-v0.3.1 and passing its source/topology/identity admission gates;
- `STATIC_READY_PROVIDER_ANCHORS.jsonl` and `STATIC_READY_PRIMARY_SEEDS.jsonl`.

The E010 parent is **not required** to have `full_campaign_gate_pass=true` or `publication_ready_geometry_layer=true`. Those global flags are known to be false for E010-v0.3.1; E011 is the explicit downstream admitted subset.

## Mode populations

- `BASIC`: up to 8 E011 deterministic provider anchors, topology/provider round-robin.
- `FULL`: all E011 deterministic provider anchors. This is the default cross-provider science campaign.
- `CERTIFY`: all E011 primary `STATIC_READY` upstream carriers. Same-provider variants are correlated; X0 collapses them to one provider vote and reports disagreement as `INTERNAL_INCONSISTENCY`.

Supported E011 source representations are `xyz`, `vect`, and `gilbert_ab_record`. Raw source SHA-256 is verified exactly. Gilbert carriers are reconstructed from the immutable catalogue plus the pinned record identity; their sampled floating-point geometry hash is not used as a cross-platform hard gate.

## X0

X0 compares H2/H3/P3/P4/P5/P6 states for the same blind topology across distinct upstream provider groups. It requires at least two providers and agreement fraction `>= 0.80`. Provider identity remains HMAC-opaque until reveal.

## Run

Place this instance at:

```text
SST-Workbench\01_research\A_falsifiers\A016_helmholtz_vortex_transport\A016-v0.2.2
```

with E011 at:

```text
SST-Workbench\01_research\E_pipelines\E011_sklsa_selected_knot_link_seed_atlas\E011-v0.3.0
```

Then:

```bat
run_all.cmd SELFTEST
run_all.cmd BASIC
run_all.cmd FULL
run_all.cmd CERTIFY
run_all.cmd REVEAL
```

`run_all.cmd` performs an E011 preflight before BASIC/FULL/CERTIFY so a missing or invalid upstream atlas fails immediately with a readable diagnostic instead of wasting a science run.
