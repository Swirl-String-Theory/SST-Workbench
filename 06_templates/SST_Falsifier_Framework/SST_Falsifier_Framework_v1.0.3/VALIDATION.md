# SST Falsifier Framework v1.0.3 — Validation Record

Validation date: 2026-10-07

## Verified in this release environment

- Python framework test suite: **35 / 35 PASS**.
- Raw `instance_template/report/FALSIFIER_REPORT.tex`: compiled successfully with `pdflatex` to a **7-page A4** document.
- New PDF publication helper: a TeX report nested under `A056-v0.2.0/A056-v0.2.0-outputs/BLIND/` was compiled with isolated auxiliary files and published as sibling artifact `A056-v0.2.0_FALSIFIER_REPORT.pdf`.
- PDF render was re-rendered and visually inspected; no clipping/overlap/broken glyphs were observed in the A056 smoke report.
- Create-once preregistration, gate-DAG enforcement, HMAC opaque identifiers, nonced reveal commitments, blind contamination scanning and deterministic packaging remain covered by regression tests.
- Strict backend authority remains enforced: a Python fallback cannot satisfy a C++/SYCL certification or screening lane.
- C++ compiler-provenance parser remains fixed: actual setuptools/MSVC `cl.exe`, compiler family, version, toolset, Python ABI and flags are fingerprinted instead of unrelated `c++.exe` instances on `PATH`.
- Intel oneAPI DD32 linker repair is unit-tested: when `LIB` lacks `libmmd.lib`, the builder locates the compiler-local library and prepends its directory to `LIB`, recording both effective `LIB` and `libmmd_path` in provenance.
- DD32 remains `dd32-fp32x2`, `SCREENING_ONLY`, **not IEEE FP64**.
- Replication-evidence regression tests enforce explicit evidence classes and prevent synthetic source-group labels from satisfying scientific cross-source replication.
- A056 synthetic-control regression: G0–G4 PASS; `G5_CONTROL_REPLICATION=PASS`; `G5_CROSS_SOURCE_REPLICATION=NOT_RUN_PREREQUISITE`; G6 NOT_RUN_PREREQUISITE; scientific conclusion `UNRESOLVED`.

## Target-machine evidence inherited from the reported v1.0.2 run

The supplied v1.0.2 target-machine selftest established:

- Windows C++/OpenMP backend available and numerically equivalent to Python FP64.
- Actual compiler provenance correctly identified Visual Studio 2022 MSVC `cl.exe` / toolset 14.44 / CPython 3.14.
- The v1.0.2 SYCL build reached Intel oneAPI `icpx` but failed at the Windows linker with `LNK1104: cannot open file 'libmmd.lib'` after adding `-fp-model=precise` for DD32.

v1.0.3 directly targets that failure by compiler-local `libmmd.lib` discovery and `LIB` augmentation.

## Target-machine checks still required

This Linux validation environment has no Intel Arc/oneAPI Windows device. Therefore v1.0.3 does **not** claim target-hardware execution of the repaired SYCL/DD32 lane.

Run locally:

```bat
run_all.cmd ALL
```

or DD32 only:

```bat
run_all.cmd DD32
```

Expected machine-readable outputs:

```text
build/BACKEND_SELFTEST.json
build/DD32_PARITY_SMOKE.json
```

The repaired SYCL build provenance should include a non-null `libmmd_path`; the device probe should identify the Intel Arc A770; FP32 and DD32 parity gates should then execute normally.

## Release criterion

The source release is acceptable only if `tools/check_release_clean.py` reports no generated binary/cache contamination and the distributed source tree matches `PACKAGE_MANIFEST.json`.
