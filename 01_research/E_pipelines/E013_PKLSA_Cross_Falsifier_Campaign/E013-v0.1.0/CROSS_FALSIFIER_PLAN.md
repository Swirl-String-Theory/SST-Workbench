# E011 — PKLSA Cross-Falsifier Requalification Campaign v0.1.0

## Purpose

This campaign intentionally **does not consume scientific conclusions or result tables from legacy falsifier outputs**.

Reusable from older falsifiers are only methods, equations, gate logic, and code that is independently re-run. Every participating falsifier must re-run from a **single newly frozen PKLSA carrier manifest** generated from the current E010 production release.

The campaign is an orchestration pipeline, not a new physics claim by itself.

## Core rule

A legacy result is never evidence in E011.

A participating falsifier may enter the campaign only when it declares a `cross_falsifier_contract.json` with:

1. `input_geometry_source = "PKLSA_COMMON_CARRIER_MANIFEST"`;
2. `forbid_legacy_outputs = true`;
3. `pklsa_required = true`;
4. an exact accepted PKLSA release identifier;
5. a run command that creates a fresh output tree.

The orchestrator sets:

```text
SST_CROSS_FALSIFIER=1
SST_DISABLE_LEGACY_RESULTS=1
SST_CROSS_REQUIRE_PKLSA=1
SST_CROSS_CARRIER_MANIFEST=<fresh manifest>
SST_PKLSA_RELEASE_ROOT=<current E010 release>
SST_CROSS_CAMPAIGN_ID=<campaign id>
SST_CROSS_OUTPUT_ROOT=<campaign output root>
```

If a falsifier ignores this contract, it must not be registered in E011.

## Topology scope

The initial campaign deliberately stays small.

### Primary SST hypothesis set

| Topology | Role |
|---|---|
| `3_1` | trefoil single-component reference / electron-sector candidate |
| `5_2` | historical SST/VAM twist-knot quark candidate A |
| `6_1` | historical SST/VAM twist-knot quark candidate B |
| `L2a1` | Hopf-link propagation / linked-state candidate |
| `L4a1` | Solomon-link interaction/detection candidate |
| `L6a4` | Borromean three-component compound/control |

### Mandatory controls

| Topology | Role |
|---|---|
| `0_1` | unknot/circle geometric null |
| `4_1` | achiral figure-eight control |

### Extended controls

Used in FULL/CERTIFY, not required in BASIC:

| Topology | Role |
|---|---|
| `5_1` | same-crossing torus-knot control against `5_2` |
| `6_2` | non-canonical six-crossing control against `6_1` |

No general sweep through all knots/links to 11 crossings is part of E011-v0.1.0.

## Carrier policy

For each topology the subset builder selects independent PKLSA carriers using a deterministic diversity-first policy.

| Profile | Carriers per topology | Intended use |
|---|---:|---|
| BASIC | 1 | plumbing / contract / quick numerical sanity |
| FULL | 3 | primary scientific run |
| CERTIFY | 3 | same source carriers, stricter resolution/backend certification |

The selector prefers distinct source/independence groups and never counts byte-identical or declared duplicate carriers as independent evidence. The exact selected carrier IDs are frozen in `CROSS_CARRIER_MANIFEST.json` before downstream execution.

## Scientific stages

### Stage 0 — PKLSA source freeze
- locate E010 current production output;
- verify release/campaign metadata;
- resolve the selected topology set;
- choose independent carriers;
- hash and freeze `CROSS_CARRIER_MANIFEST.json`.

### Stage 1 — Geometry and topology
Freshly recompute arclength/reach, ropelength, curvature/torsion, writhe/linking, topology identity, and provider/source independence.

### Stage 2 — Finite-core energy and state selection
Freshly recompute finite-core/line energy, gradients/stationarity, perturbations, restoring response, topology preservation, and convergence. A relaxed/stationary state is a result to demonstrate, not an assumed preprocessing step.

### Stage 3 — Local dynamics
For dynamically admissible carriers: Hessian, Jacobian, Kelvin modes, ringdown, and RPO/Floquet only when prerequisites are actually met.

### Stage 4 — Phase/chirality/model diagnostics
Fresh data only: circulation-relative chirality, circular/Fourier phase representation, optional SG/KG/Duffing and exponential/stretched/bi-exponential/Mittag-Leffler comparisons.

### Stage 5 — Action / scale closure
Run fresh same-mode energy/frequency pairing, amplitude independence, spatial/temporal convergence, provider universality, plus the separate QGI/fluid specific-action lane where provenance-clean data exist.

### Stage 6 — Master-Mass reconstruction
Only after upstream fresh measurements exist: compare geometric kernels, hyperbolic-volume/topological candidates, finite-core energy kernels, and state-selected dynamic kernels; freeze target-free predictions; reveal protected mass labels/targets only after protocol eligibility.

## Cross-falsifier evidence matrix

The integrated campaign should produce one row per `(topology, carrier, resolution)` with column families:

```text
identity / provenance
geometry
finite-core energy
stationarity
restoring response
Hessian/Jacobian spectrum
phase/chirality
action diagnostics
mass-kernel predictors
numerical convergence
backend parity
gate status
```

This makes it possible to test mass predictors on the *same carrier population* instead of combining unrelated historical datasets.

## Failure semantics

Scientific FAIL is data. The orchestrator continues to later registered members when one falsifier has scientific FAIL or UNRESOLVED gates. Infrastructure failures remain separate and include invalid PKLSA provenance, changed common carrier manifest, attempted legacy-output consumption, invalid contract/hash, or child-process crash.

Cross-falsifier aggregation preserves `PASS`, `FAIL`, `UNRESOLVED`, `NOT_APPLICABLE`, and `RUNTIME_ERROR` as distinct states.

## Suggested upgrade order

1. E010 subset freeze / common carrier manifest.
2. A057 current PKLSA loader validation against the common manifest.
3. A054 successor: restoring/self-confinement tests rebuilt on common PKLSA carriers.
4. A055 successor: consume fresh A054-successor trajectories/Jacobians only.
5. A056 successor/current release: same selected E010 carriers and fresh perturbations.
6. A041/Wien–Planck successor: current PKLSA carriers only.
7. A042 action-gauge lane: fresh provenance-clean action data; no legacy result import.
8. A057-v0.2.x: final cross-falsifier Master-Mass model competition.

## Recommended installation target

```text
01_research/E_pipelines/
└─ E011_pklsa_cross_falsifier_campaign/
   └─ E011-v0.1.0/
```

Run:

```bat
run_all_cross_falsifier.cmd PLAN C:\workspace\projects\SST-Workbench
run_all_cross_falsifier.cmd BASIC C:\workspace\projects\SST-Workbench
run_all_cross_falsifier.cmd FULL C:\workspace\projects\SST-Workbench
run_all_cross_falsifier.cmd CERTIFY C:\workspace\projects\SST-Workbench
```

`PLAN` performs source/contract discovery without launching child falsifiers. `BASIC`, `FULL`, and `CERTIFY` first build/freeze a fresh common carrier manifest and then run only packages that explicitly opted into the current cross-falsifier contract.
