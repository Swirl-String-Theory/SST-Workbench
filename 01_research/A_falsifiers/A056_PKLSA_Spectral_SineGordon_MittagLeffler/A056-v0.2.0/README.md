# A056 PKLSA Spectral--Sine-Gordon--Mittag-Leffler Falsifier v0.2.0

**Catalog:** A056  
**Framework:** first consumer test of `SST Falsifier Framework v1.0.0.dev0`  
**Mode:** blind, fail-closed, CPU-authoritative

A056 asks two independent questions of time-dependent vortex-filament data:

1. Is the effective phase/torsion dynamics better described by a Sine--Gordon restoring law than Wave, Klein--Gordon, or Duffing alternatives?
2. Is the relaxation better described by a Mittag--Leffler fractional-memory law than ordinary exponential alternatives?

v0.2.0 is specifically designed to test the new shared falsifier framework while tightening the science relative to v0.1.0.

## Key change from v0.1.0

The package now separates **blind discovery** from **held-out confirmation**, then requires **numerical certification** before cross-source replication can promote a result. Static PKLSA curves are not accepted as a substitute for \(\varphi(s,t)\).

## Framework gate chain

```text
G0 provenance
 -> G1 admissibility
 -> G2 blind discovery
 -> G3 held-out confirmation
 -> G4 numerical certification
 -> G5 cross-source replication
 -> G6 joint mechanism/physics
 -> REVEAL
```

Every gate ends in `PASS`, `FAIL`, `UNRESOLVED`, or `NOT_RUN_PREREQUISITE`.

## Quick start

```bat
run_all.cmd basic
```

For the framework itself without requiring a native extension:

```bat
run_25_framework_smoke.cmd
```

For a real dynamic-provider directory:

```bat
run_real_blind.cmd D:\path\to\provider_output full
```

The real provider directory must contain matched `.npz`/`.json` pairs satisfying `A056-DYNAMIC-PROVIDER-2`.

## Native and GPU roles

The scientific reference path is Python/CPU. `cpp/native.cpp` is an independently checked C++17/OpenMP implementation of the finite-difference and Mittag--Leffler kernels. The optional SYCL path uses a separate worker process, never SYCL device code inside the CPython `.pyd`; v0.2.0 uses it as a hardware/architecture probe only.

## Outputs

The default output directory is:

```text
./<package-folder>-outputs/

For the Workbench layout `A056-v0.2.0`, this resolves to:

```text
./A056-v0.2.0-outputs/
```
```

The package creates separate BLIND and REVEALED archives and SHA-256 sidecars.

## Interpretation boundary

A synthetic-control PASS validates implementation logic only. Real scientific support requires provider-native time-dependent data, frozen phase semantics, numerical certification, and independent source-group replication.


## Output-path hotfix (2026-10-07)

The pipeline, reveal, report and packaging stages now all resolve the default output directory through the same framework function `default_output_dir(ROOT)`. This is required because the Workbench version folder is named `A056-v0.2.0`, while the scientific package name is longer. The previous pipeline hard-coded the long scientific name and could therefore write to a different directory than the reveal stage expected.
