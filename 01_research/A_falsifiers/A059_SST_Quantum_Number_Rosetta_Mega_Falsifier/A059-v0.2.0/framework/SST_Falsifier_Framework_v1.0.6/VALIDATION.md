# SST Falsifier Framework v1.0.6 — Canonical Validation Record

Freeze date: 2026-10-07  
Status: **CANONICAL_FROZEN**

## Source lineage

v1.0.6 is based on the immutable v1.0.4 canonical archive:

- `SST_Falsifier_Framework_v1.0.4.zip`
- SHA-256: `1bdf8a20f0f0cbdf86ab89fb198d1930e0694579dee8d5dcd35149972c0d2104`

The following three v1.0.5 artifacts were independently reviewed and selectively consolidated:

- Python-path candidate: `8ebbb5a42970253a7b3783d85b4da062da3ad75c96f2dad71f082e08ed35bce9`
- prior `v1.0.5-CANONICAL_FROZEN` artifact: `7b8cc9ca5317c7f7162b1ab9ad062dec958000ab3d14f95e87107b048c2a0302`
- reveal-orchestration candidate: `6190666bb65c0de9991e5278557b4fa52d579be73966343209753726253f4083`

None of those v1.0.5 artifacts is itself the canonical production release after this consolidation.

## Regression validation

The v1.0.6 source tree was run with bytecode generation disabled:

```text
54 passed
```

The regression suite includes the existing scientific/backend/report/G5 tests plus new checks for:

- generated `run_python` launcher contract;
- pytest import bootstrap without an environment override;
- explicit locator pin winning over a preloaded stale framework;
- invalid `.sst_framework_root` failing closed;
- invalid explicit `SST_FALSIFIER_FRAMEWORK_ROOT` failing closed before a valid locator;
- module launch using both instance-local packages and the pinned framework;
- exact output-manifest verification;
- reveal policy for NOT_RUN, completed negative discovery and UNRESOLVED states;
- gate-ledger self-hash tamper detection;
- `RUN_SUMMARY` -> gate-ledger hash mismatch detection;
- output-tree/manifest tamper detection;
- complete stale reveal cleanup including post-run discussion and parent PDF;
- `REVEAL_DECISION.json` being written before and included in the revealed ZIP.

## Backend scope and target-machine evidence

No numerical backend source was changed from v1.0.4 in this release. Python reference, C++/OpenMP, SYCL FP32, DD32 arithmetic, precision thresholds and compiler/linker setup remain unchanged.

The retained target-machine evidence therefore documents the unchanged backend implementation:

- `validation/hardware/2026-10-07_arc-a770/BACKEND_SELFTEST.json`
  - SHA-256 `106c1866557e1cf8c1dc4f91fad84337214ecd452b7694abda20e92b0e86da9c`
  - overall PASS
- `validation/hardware/2026-10-07_arc-a770/DD32_PARITY_SMOKE.json`
  - SHA-256 `a40691e96d521154b2f11de06dcb90b4d05aafbf474ce1e75e9ac313319ad3db`
  - overall PASS
- device: Intel Arc A770
- C++ FP64: certification lane
- DD32/FP32x2: screening-only high-precision lane; not IEEE FP64

A fresh target-machine `run_all.cmd ALL` is recommended after installation, but no new hardware claim is inferred from the orchestration-only changes in v1.0.6.

## Reveal integrity result

v1.0.6 no longer trusts gate statuses in isolation. Reveal requires internal agreement among the blind gate ledger, its self-hash, the run-summary binding and the exact output manifest/tree before frozen policy and commitment checks can authorize disclosure.

## Canonical policy

Use v1.0.6 for all **new** falsifiers. Historical falsifier releases remain pinned to their original framework/template for reproducibility. Do not edit v1.0.6 in place; every future change requires a new framework version.

## Backend source identity against v1.0.4

The following numerical/backend files are byte-identical to v1.0.4:

```text
sst_falsifier/dd32_reference.py                 99959d4825c34b2afce5de62f0f3f1b75907c0c32ad3e17bfd565a9cc1afdec4
sst_falsifier/native_build.py                   8244aae1bf16ddc012a85f912d0425231a4cd8e2eb66fdaf15272e8d64a1a342
sst_falsifier/sycl_worker.py                    1dbcf574aadfafeeabd74e107c66f8a73cbd871f24a378f10ba223a961d9c053
sst_falsifier/backends/cpp_pybind.py            9c22a5ef2b8f8dc6044a86320810c194d0d0cd1bf9bb15b0ce7dd5139685f3ea
sst_falsifier/backends/python_ref.py             99d0c876942f734ca01b496acdf5eefb97e0a031e527495a1209b022e2b4e74b
instance_template/native/cpp/native.cpp          bff7e885437cd7f82033c79e38a02acd798184a41ea0aeaece58e9bcf55fe08f
instance_template/native/cpp/sycl_worker.cpp     cd157b1cbb19b7daa6a939ef4371c51da1988db5b3b783d01b27f82a7db7d92e
```

## Release hygiene

Before manifest generation:

```text
Python source syntax check: 49 files compile
Release contamination scan: []
Canonical source files (excluding package manifest + sidecar): 92
```

The final archive therefore contains 94 files: 92 canonical source/evidence files plus `PACKAGE_MANIFEST.json` and `MANIFEST_SHA256.txt`.
