# A056 PKLSA Spectral--Sine-Gordon--Mittag-Leffler Falsifier v0.2.1

**Catalog:** A056  
**Framework target:** `SST Falsifier Framework v1.0.2` (`1.0.2.dev0` snapshot)  
**Mode:** blind, fail-closed, CPU/FP64-authoritative

A056 asks two independent questions of provider-native vortex-filament dynamics:

1. Is the effective phase/torsion field better described by a Sine--Gordon restoring law than Wave, Klein--Gordon, or Duffing alternatives?
2. Is the relaxation better described by a Mittag--Leffler fractional-memory law than exponential, stretched-exponential, or bi-exponential alternatives?

v0.2.1 upgrades the first framework consumer from the earlier `1.0.0.dev0` snapshot to the recovered v1.0.2 development contract and backports the Gate-5 evidence-class fix intended for framework v1.0.3.

## Framework v1.0.2 integration

The package now exercises:

- exact-version `.sst_framework_root` discovery rather than path-depth assumptions;
- deterministic local output resolution: `A056-v0.2.1-outputs`;
- actual native compiler/build provenance and a hash-bound build fingerprint;
- `run_02_backend_selftest.cmd` with Python-FP64 vs C++-FP64 parity;
- external, content-addressed oneAPI/SYCL worker isolation;
- optional DD32 / FP32x2 precision smoke compiled with precise FP semantics;
- explicit backend authority metadata in BLIND provenance;
- mandatory LaTeX report generation.

DD32 is explicitly **not IEEE FP64**.  It is an experimental screening lane; final scientific promotion remains CPU/Python or C++ FP64 certified.

## Gate chain

```text
G0 provenance
 -> G1 admissibility
 -> G2 blind discovery
 -> G3 held-out confirmation
 -> G4 numerical certification
 -> G5 control replication
 -> G5 physical cross-source replication
 -> G6 joint mechanism/physics
 -> REVEAL
```

Every gate terminates in `PASS`, `FAIL`, `UNRESOLVED`, or `NOT_RUN_PREREQUISITE`.

### Gate-5 evidence rule

Provider metadata must declare:

```text
evidence_class = synthetic_control | simulation | independent_source | experimental
```

Synthetic cases from one generator no longer become "independent" merely because they have different `source_group` labels.  `synthetic_control` and `simulation` are excluded from physical cross-source replication.  Only `independent_source` and `experimental` can satisfy `G5_CROSS_SOURCE_REPLICATION`.

The synthetic regression population should therefore end with:

```text
G5_CONTROL_REPLICATION      = PASS
G5_CROSS_SOURCE_REPLICATION = NOT_RUN_PREREQUISITE
G6_MECHANISM_PHYSICS        = NOT_RUN_PREREQUISITE
conclusion                  = JOINT_CONTROL_RECOVERED
```

That is implementation validation, not SST evidence.

## Quick start

```bat
run_all.cmd basic
```

This executes install/build, compiler-provenance capture, backend selftest, framework/science tests, blind synthetic campaign, reveal regression, LaTeX report generation, and packaging.

Optional Arc/SYCL DD32 smoke:

```bat
run_35_sycl_worker_smoke.cmd
```

For a real dynamic provider:

```bat
run_real_blind.cmd D:\path\to\provider_output full
```

Real input must be matched `.npz`/`.json` pairs satisfying `A056-DYNAMIC-PROVIDER-3`; static XYZ geometry alone is inadmissible.

## Output contract

For the canonical Workbench folder

```text
...\A056_PKLSA_Spectral_SineGordon_MittagLeffler\A056-v0.2.1\
```

the default output is exactly

```text
A056-v0.2.1\A056-v0.2.1-outputs\
```

and packaging creates

```text
A056-v0.2.1-outputs.zip
A056-v0.2.1-outputs_BLIND.zip
A056-v0.2.1-outputs_REVEALED.zip
```

with SHA-256 sidecars.

## Interpretation boundary

A synthetic-control recovery validates code/model-selection logic.  A physical SST conclusion additionally requires provider-native dynamics, frozen phase semantics, numerical certification, and at least two admissible physically independent replication groups.
