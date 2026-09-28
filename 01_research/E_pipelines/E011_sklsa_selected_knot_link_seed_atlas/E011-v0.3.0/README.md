# E011 SKLSA — Provider Agreement + STATIC_READY Seed Atlas v0.3.0

E011-v0.3.0 turns the v0.2.0 literature-gated carrier selection into a falsifier-facing **static seed atlas**. It still consumes E010-v0.3.1 as the authoritative geometry/source/topology qualification layer.

## What v0.3.0 adds

1. **Provider agreement:** all independent upstream `STATIC_READY` seeds are grouped by provider; agreement compares provider medians observable-by-observable while retaining within-provider spread. No composite best-seed score is introduced.
2. **Empirical uncertainty envelopes:** median, MAD, min/max, absolute span, relative span and relative half-span are emitted per topology/observable.
3. **Definitive `STATIC_READY` seedsets:** seeds are admitted by explicit numeric/provenance capability gates, not by directory presence or visual preference.
4. **Seed capabilities:** `writhe_ready`, `acn_ready`, `ropelength_ready`, `reach_ready`, curvature and torsion flags allow downstream falsifiers to request what they actually need.
5. **Actionable provenance:** E010 source metadata is carried into every seed locator: carrier ID, source path/reference ID, representation, raw SHA-256 and geometry SHA-256.
6. **Machine seed contract:** `SEED_CONTRACT_SCHEMA.json` defines how falsifiers should request atlas seeds.

## STATIC_READY definition

A primary static seed must:

- be an E010 literature-hard-gate PASS carrier;
- not be a mirror or unclassified artifact;
- represent an independent upstream provider;
- have `RESOLVED` status for the static core observables `Wr`, `ACN`, `dcsd`, and `kappa_rms`.

`Rop`, `Thi`, `reach`, `kappa_max`, `sigma_kappa`, and `tau_rms` are **capabilities**, not blanket requirements. A ropelength falsifier must explicitly request `ropelength_ready`; a torsion falsifier must request `torsion_rms_ready`.

A mirror can never become `STATIC_READY`. Generated/derived non-mirror geometries may be exported as secondary/control seeds but never create upstream-provider evidence.

## Provider agreement

Provider agreement uses all independent upstream primary `STATIC_READY` seeds, grouped by provider. Each provider contributes one median per observable; within-provider min/max/MAD are retained as uncertainty. Shape agreement uses `|Wr|`; signed `Wr` remains reported separately so orientation/chirality reversal is never hidden.

One deterministic **provider anchor** is also exported per provider for convenient falsifier execution. Anchor selection uses provenance/source stage (e.g. `FINAL` before historical intermediate), capability completeness, resolution and stable carrier ID; no SST observable value is optimized.

The agreement bands in `configs/static_ready_policy.json` are transparent analysis-policy tolerances, **not physical constants and not fitted to SST predictions**. A topology can therefore be `STATIC_READY` while being `CROSS_PROVIDER_SENSITIVE`; this is valuable uncertainty information rather than grounds for choosing the convenient provider.

Statuses:

- `CROSS_PROVIDER_ROBUST`
- `CROSS_PROVIDER_SENSITIVE`
- `CROSS_PROVIDER_INCOMPLETE`
- `SINGLE_PROVIDER_QUALIFIED`
- `STATIC_NOT_READY_E010_EXCLUDED`
- `STATIC_NOT_READY_CORE_OBSERVABLES`
- `STATIC_NOT_READY_MIRROR_ONLY`
- `STATIC_NOT_READY_NO_UPSTREAM_REFERENCE`

## Run

```bat
run_all.cmd C:\workspace\projects\SST-Workbench
```

For exact reproduction against an E010 archive:

```bat
run_all.cmd C:\workspace\projects\SST-Workbench C:\workspace\projects\SST-Workbench\01_research\E_pipelines\E010_pklsa_parametric_knot_link_seed_atlas\E010-v0.3.1\E010_PKLSA_Production_Knot_Link_Basis_v0.3.1-outputs.zip
```

## Principal outputs

- `STATIC_READY_INDEX.json/.csv`
- `STATIC_READY_SEEDSETS.json`
- `STATIC_READY_PRIMARY_SEEDS.jsonl`
- `STATIC_READY_SECONDARY_SEEDS.jsonl`
- `STATIC_READY_CONTROL_SEEDS.jsonl`
- `PROVIDER_AGREEMENT.json/.csv`
- `SEED_CONTRACT_SCHEMA.json`
- inherited audit artifacts from v0.2.0
- `topologies/<ID>/STATIC_READY_SEEDSET.json`

## Scientific boundary

`STATIC_READY` means a carrier is provenance-clean and numerically qualified for **static centerline geometry** analysis under the declared capability flags. It is explicitly **not** `DYNAMICS_READY`: v0.3.0 does not certify finite-core Biot–Savart evolution, self-confinement, Kelvin modes, Floquet stability, or an SST particle identification.