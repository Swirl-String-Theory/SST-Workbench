# E013 — PKLSA Cross-Falsifier Requalification Campaign v0.1.1

## Why E013

E011 is the SKLSA selected/static-ready seed atlas.
E012 is the PKLSA dynamic eigenmode extractor.
E013 is therefore the next pipeline identity for the cross-falsifier requalification campaign.

E013 is downstream of the current PKLSA/SKLSA chain and must not reuse historical falsifier
result tables as scientific evidence.

## Authority chain

```text
E010 PKLSA production geometry/source/topology qualification
        ↓
E011 SKLSA STATIC_READY atlas + provider anchors
        ↓
E012 PKLSA dynamic eigenmode extractor (optional dynamic handoff where applicable)
        ↓
E013 cross-falsifier requalification
        ↓
fresh A-falsifier results on one common carrier population
```

E013 uses E011-v0.3.0 as the authoritative source of STATIC_READY carrier identities.
It does not independently reinterpret E010 geometry_metrics.jsonl.

## Scientific rule

Old falsifier outputs are not evidence.

Reusable:
- equations;
- algorithms;
- gate definitions;
- source code;
- backend implementations.

Not reusable as evidence:
- old PASS/FAIL verdicts;
- old spectra;
- old relaxed states;
- old energies;
- old mass fits;
- old carrier means;
- old provider comparisons.

Every participating falsifier must re-run against the frozen E013 common carrier manifest.

## Requested topology set

### Required core
- `3_1` — trefoil reference / electron-sector candidate
- `5_2` — historical SST/VAM twist-knot candidate A
- `6_1` — historical SST/VAM twist-knot candidate B
- `4_1` — achiral control

### Preferred link
- `L2a1` — Hopf link; currently E011 SINGLE_PROVIDER_QUALIFIED

### Extended controls
- `5_1` — same-crossing control for `5_2`
- `6_2` — same-crossing control for `6_1`

### Requested but availability-gated
- `L4a1` — Solomon link
- `L6a4` — Borromean rings
- `0_1` — unknot/null if a future E011 release supplies it

A requested topology that is not STATIC_READY in the authoritative E011 release is recorded as
`NOT_AVAILABLE_STATIC_READY` and does not abort the entire campaign.

With the current E011-v0.3.0 atlas, `L4a1` and `L6a4` are selected upstream but are not
STATIC_READY because no literature-admitted carrier was available. E013 must preserve that status
instead of substituting an arbitrary geometry.

## Carrier selection

E013 selects only E011 `STATIC_READY_PROVIDER_ANCHORS.jsonl`.

This is deliberate:
- provider anchors are selected by provenance/stage/capability/resolution;
- no SST observable value is optimized;
- provider identity remains explicit;
- the same anchor IDs can be handed to every downstream falsifier.

Profiles:
- PLAN: inventory only, no child falsifiers;
- BASIC: one deterministic provider anchor per available topology;
- FULL: up to two independent provider anchors per topology;
- CERTIFY: same provider-anchor population as FULL; downstream falsifiers increase their own
  resolution/backend certification rather than silently changing carrier identity.

Single-provider topology evidence is allowed to run but retains its lower evidence status.

## Member contract

A participating falsifier needs `cross_falsifier_contract.json`:

```json
{
  "schema": "SST-CROSS-FALSIFIER-MEMBER-2",
  "enabled": true,
  "catalog_id": "A057",
  "version": "v0.2.0",
  "stage": 60,
  "input_geometry_source": "E013_COMMON_SKLSA_PROVIDER_ANCHORS",
  "forbid_legacy_outputs": true,
  "sklsa_required": true,
  "accepted_sklsa_release_ids": ["E011-v0.3.0"],
  "run": {
    "working_directory": ".",
    "command": "run_all.cmd",
    "args": ["{profile}", "{workbench_root}"]
  }
}
```

E013 sets:
- `SST_CROSS_FALSIFIER=1`
- `SST_DISABLE_LEGACY_RESULTS=1`
- `SST_CROSS_REQUIRE_SKLSA=1`
- `SST_CROSS_CARRIER_MANIFEST=<...CROSS_CARRIER_MANIFEST.json>`
- `SST_SKLSA_RELEASE_ROOT=<E011-v0.3.0>`
- `SST_CROSS_CAMPAIGN_ID=<...>`
- `SST_CROSS_OUTPUT_ROOT=<...>`

A child package that does not explicitly consume the E013 carrier manifest is not campaign evidence.

## Failure semantics

Scientific FAIL is retained and the campaign continues.

The campaign distinguishes:
- PASS / FAIL / UNRESOLVED / NOT_APPLICABLE: scientific child-gate states;
- NOT_AVAILABLE_STATIC_READY: upstream topology availability;
- RUNTIME_ERROR: child execution failure;
- INFRASTRUCTURE_FAIL: E011 source/provenance/manifest failure.

## Run

```bat
run_all_cross_falsifier.cmd PLAN C:\workspace\projects\SST-Workbench
run_all_cross_falsifier.cmd BASIC C:\workspace\projects\SST-Workbench
run_all_cross_falsifier.cmd FULL C:\workspace\projects\SST-Workbench
run_all_cross_falsifier.cmd CERTIFY C:\workspace\projects\SST-Workbench
```

PLAN and BASIC are useful before any A-falsifier has been upgraded. If no member contracts exist,
E013 returns success with `READY_NO_MEMBERS` after proving that the common carrier manifest can
be constructed.

## Recommended next upgrades

1. A057 successor: consume E013 common anchors and rerun energy/Lagrangian/Hamiltonian/Jacobian.
2. A054 successor: fresh restoring/self-confinement experiment on the same anchors.
3. A055 successor: fresh chirality/Jacobian analysis on trajectories generated in this campaign.
4. A056 successor: fresh phase-model analysis on the same carrier identities/perturbation contract.
5. A041/A042 successor where relevant for action/scale closure.
6. Final E013 aggregation: join only fresh outputs by `static_seed_id`, `carrier_id`,
   `geometry_sha256`, topology and provider.
