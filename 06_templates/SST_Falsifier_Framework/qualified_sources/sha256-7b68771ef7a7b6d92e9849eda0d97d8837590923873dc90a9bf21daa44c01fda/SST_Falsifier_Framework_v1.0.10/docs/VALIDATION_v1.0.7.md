# SST Falsifier Framework v1.0.7 — Canonical Validation Record

Freeze date: 2026-10-07  
Status: **CANONICAL_FROZEN**

## Parent integrity

v1.0.7 was built directly from the user-supplied canonical v1.0.6 archive, not from an independently reconstructed copy:

- parent archive: `SST_Falsifier_Framework_v1.0.6-CANONICAL_FROZEN(1).zip`
- parent ZIP SHA-256: `24629848e3befcde67c02a935fc78347560ac42107043fbc14aaabdf146ee60d`
- parent `PACKAGE_MANIFEST.json` SHA-256: `233730abad5ef26f851db0ae75c691fd17daa75e99beb8419d6934ccf85c15be`
- parent package verification: **92/92 files match**

## Maintenance change

The only functional runtime change is in `sst_falsifier/blind.py`.

The forbidden-term scanner now treats standard runtime/build/vendor directories as outside falsifier-owned scientific source:

```text
.venv
venv
env
__pycache__
.pytest_cache
build
dist
.git
.mypy_cache
.ruff_cache
node_modules
```

This prevents third-party dependencies (for example SciPy constants containing terms such as `proton` or `neutron`) from causing false blind-contamination failures.

Falsifier-owned source, configuration, reports and blind outputs remain scanned. `private`, `revealed` and `reveal_private` retain their existing v1.0.6 treatment.

## Regression validation

Full framework regression suite:

```text
56 passed
```

New regression coverage proves both sides of the ownership rule:

1. a forbidden term inside runtime/vendor trees such as `.venv/Lib/site-packages/...` is ignored;
2. the same forbidden term in instance-owned source is still detected and therefore remains fail closed.

Additional release validation:

```text
Python syntax check: 49 files PASS
Release contamination scan: []
Canonical source/evidence files: 92
```

## Unchanged v1.0.6 runtime/backends

The following critical files are byte-identical to the user-supplied v1.0.6 parent:

```text
sst_falsifier/dd32_reference.py                 99959d4825c34b2afce5de62f0f3f1b75907c0c32ad3e17bfd565a9cc1afdec4
sst_falsifier/native_build.py                   8244aae1bf16ddc012a85f912d0425231a4cd8e2eb66fdaf15272e8d64a1a342
sst_falsifier/sycl_worker.py                    1dbcf574aadfafeeabd74e107c66f8a73cbd871f24a378f10ba223a961d9c053
sst_falsifier/backends/cpp_pybind.py            9c22a5ef2b8f8dc6044a86320810c194d0d0cd1bf9bb15b0ce7dd5139685f3ea
sst_falsifier/backends/python_ref.py             99d0c876942f734ca01b496acdf5eefb97e0a031e527495a1209b022e2b4e74b
instance_template/native/cpp/native.cpp          bff7e885437cd7f82033c79e38a02acd798184a41ea0aeaece58e9bcf55fe08f
instance_template/native/cpp/sycl_worker.cpp     cd157b1cbb19b7daa6a939ef4371c51da1988db5b3b783d01b27f82a7db7d92e
sst_falsifier/runner.py                          3feff2952e2a9feb9cf5b626c8bbfcdaeeef2e22f3380c69316ba5ce196c67c1
sst_falsifier/outputs.py                         cd586140835f7ac9dfd6c42b7d29f664f3747633c861f80c82b141f7a0c602ab
sst_falsifier/gates.py                           7a5f28350b9fdc2747208152877fb3645c8c53465a87b470ecf7a322610a81e4
sst_falsifier/protocol.py                        594c03d156b75b3e9cf812b8c0b53e3f8ed8167566260db72cbc47c9e479dc7b
instance_template/framework_bootstrap.py         050c1768026701f655e424e0d2faff7a8ff3b06d8ee206f6e1b86783d3c3ec14
instance_template/conftest.py                    be898d5f37fd2dae23e4c62588f4e3060c3c3b8077bcde6eb150e10fcd6696dc
instance_template/run_python.py                  8010f159e8e618d9f23673f1a6d98559f644b8fd44b6674ac0546f08de7aa010
```

No numerical kernel, C++/OpenMP/SYCL/DD32 implementation, precision threshold, gate semantics, reveal-integrity rule, bootstrap precedence or backend authority changed.

## Hardware evidence

Because all numerical/backend sources are byte-identical to v1.0.6, the retained Arc A770 backend evidence remains provenance evidence for the unchanged implementation. A new target-machine `run_all.cmd ALL` may be run after installation, but v1.0.7 makes no new hardware-performance or numerical-precision claim.

## Canonical policy

Use v1.0.7 for new falsifiers. Keep historical falsifiers pinned to their original framework versions for reproducibility. Do not edit v1.0.7 in place; any future change requires a new framework version.
