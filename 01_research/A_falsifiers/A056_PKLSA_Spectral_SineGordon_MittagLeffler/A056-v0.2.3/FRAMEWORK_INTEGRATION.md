# A056 v0.2.3 / SST Falsifier Framework v1.0.4 integration

A056 v0.2.3 is regenerated from `SST_Falsifier_Framework_v1.0.4-CANONICAL_FROZEN` rather than patched forward from the vendored development framework used by A056 v0.2.2.

## Pin

`FRAMEWORK_PIN.json` records the canonical framework version, frozen status, canonical Workbench path, source ZIP SHA-256, package-manifest hash, and retained target-machine backend/DD32 validation hashes.

## Shared framework responsibilities

v1.0.4 owns protocol freeze/verification, nonced blind/reveal commitments, gate DAG semantics, source/environment/output manifests, deterministic BLIND/REVEALED packaging, strict backend authority, compiler provenance, external SYCL-worker/DD32 infrastructure, evidence-class-aware replication, and LaTeX-to-PDF publication.

A056 owns only the experiment-specific provider contract, finite-difference phase features, phase/ringdown competitors, spectral qualification, coarsening checks, thresholds and scientific interpretation.

## Precision authority

- Python/NumPy FP64: `REFERENCE`.
- instance-local C++17/OpenMP FP64: `CERTIFICATION`.
- SYCL FP32: `SCREENING_ONLY`.
- SYCL DD32/FP32x2: `SCREENING_ONLY`; not IEEE FP64.

The instance-local `_sst_native` module retains the framework's regularized Biot-Savart entry point for canonical backend selftests and adds A056's phase-feature and Mittag-Leffler certification kernels.

## Gate-5/G5 naming note

In the canonical framework DAG, **G5 is numerical C++ certification**. The earlier A056-v0.2.2 labels `G5_CONTROL_REPLICATION` and `G5_CROSS_SOURCE_REPLICATION` are now represented under canonical **G7 replication**, while their evidence-class split is preserved inside the G7 metrics through `sst_falsifier.replication.assess_replication`.

## Output-name compatibility

The frozen framework is not modified. A local adapter normalizes its generic `A056_v0.2.3-outputs` name to A056's established `A056-v0.2.3-outputs` Workbench convention before/after each framework invocation.

## Generated-report layout adapter

Framework v1.0.4 remains byte-immutable. Its generated `AUTO_RESULTS.tex` can contain arbitrarily long gate questions, paths and hashes. A056 therefore performs a **post-run presentation-only transformation** of this generated file into wrapped `longtable` summaries and republishes the PDF. The exact machine-readable `BACKEND_MANIFEST.json`, `SOURCE_MANIFEST.json`, `ENVIRONMENT_PUBLIC.json` and `OUTPUT_MANIFEST.json` remain authoritative and unchanged by that presentation transformation. No frozen protocol, threshold, gate definition or framework source is edited.
