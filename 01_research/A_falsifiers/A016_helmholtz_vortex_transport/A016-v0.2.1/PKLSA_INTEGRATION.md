# PKLSA v0.4.0 integration contract

A016 v0.2.1 treats PKLSA as a **geometry qualification and provenance layer**, not as proof of Euler stability.

## Required release

The E010 version root is normally:

```text
01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas/E010-v0.4.0
```

A016 requires exactly one discovered release with:

```text
schema = PKLSA-HIGH-RES-QUALIFICATION-4
atlas_version = 0.4.0
publication_ready_geometry_layer = true
```

If multiple publication-ready releases exist below that root, A016 fails closed until `release_relative_path` is pinned in `source_contract.json`.

## Carrier admission

A topology is admitted only when its:

```text
qualification/summary.json
```

contains `qualification_gate_pass=true`. Carrier descriptors are then taken from the topology's `sources/` and `generated/` branches. The carrier `source_path` is resolved without filename-only searching.

Supported geometry representations are text XYZ, `.npz`, `.npy`, and simple JSON point/component arrays. PKLSA v0.4.0 braid-route NPZ files using `component_0`, `component_1`, ... are supported directly.

## Evidence axes

A carrier retains the PKLSA fields:

```text
topology_id
carrier_id
source_family
parent_source_family / provenance_family
provider_group
independence_group
source_role
geometry_sha256
```

Public blind outputs expose only HMAC group IDs for these identity axes.

## Generated-carrier rule

Generated/derived geometry can be scientifically informative but is not an upstream replication source. In particular, the PKLSA v0.4.0 parametric braid route remains generated-from-topology evidence. Therefore generated carriers are excluded from X0 closure.

## Cross-source vote rule

The independent vote axis for X0 is `provider_group`, not file count. Within one topology and provider:

- all carrier states equal -> one provider vote;
- carrier states disagree -> `INTERNAL_INCONSISTENCY`;
- extra discretizations/variants do not create extra votes.

This prevents a provider with many carrier variants from dominating a topology-level consistency result.
