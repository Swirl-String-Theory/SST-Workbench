# SST Falsifier Framework v1.0.6

> **Status: CANONICAL_FROZEN.** v1.0.6 is the production baseline for new SST falsifiers. It consolidates the v1.0.4 canonical release with the reviewed v1.0.5 Python-path, pytest-bootstrap and reveal-orchestration hardening branches. Do not patch this directory in place; any future change requires a new framework version.

## Canonical Workbench location

```text
SST-Workbench/
└── 06_templates/
    └── SST_Falsifier_Framework/
        ├── SST_Falsifier_Framework_v1.0.4/   # historical canonical
        └── SST_Falsifier_Framework_v1.0.6/   # current canonical
```

Scientific instances remain under `01_research/A_falsifiers/...`. No framework/template lookup under `04_tools/D_proof` is used.

## Core scientific rule

A `PASS` is valid only when the preregistered source, implementation and precision class actually ran. Silent backend fallback cannot satisfy a certification gate.

## Profiles

- `minimal`: Python FP64/reference only.
- `cpu`: Python FP64 reference + strict C++/pybind11 FP64 certification.
- `gpu`: Python FP64 + C++ FP64 + SYCL FP32 screening + DD32/FP32x2 high-precision screening.
- `multilibrary_gpu`: same backend ladder plus independent multi-source discovery/confirmation contract.

## Precision lanes

```text
Python/NumPy FP64           REFERENCE
C++/pybind11 FP64          CERTIFICATION
SYCL FP32                   SCREENING_ONLY
SYCL DD32 / FP32x2         SCREENING_ONLY (high-precision candidate)
```

DD32 represents one device scalar as two binary32 values and is **not IEEE FP64**. Its exponent range remains binary32 and its nominal significand capacity is roughly 48 bits. The frozen validation evidence on the Arc A770 is retained under `validation/hardware/2026-10-07_arc-a770/`.

Default DD32 backend gates remain:

```text
velocity relative-L2              <= 1e-8
directional finite-diff rel-L2    <= 2e-6
improvement over ordinary FP32    >= 20x
```

No numerical backend kernel, compiler/linker policy or precision threshold changed from v1.0.4 to v1.0.6.

## Create a new falsifier

```bat
python tools\new_falsifier.py A057 my_falsifier ^
  C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A057_my_falsifier\A057-v0.1.0 ^
  --profile multilibrary_gpu --version v0.1.0
```

The generator writes a relative `.sst_framework_root` locator that pins the instance to the exact framework used to create it.

## Strict framework pinning

Generated instances use one shared instance-local resolver: `framework_bootstrap.py`.

Precedence is fail-closed:

1. explicit `SST_FALSIFIER_FRAMEWORK_ROOT`;
2. `.sst_framework_root`;
3. legacy autodiscovery under `06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v*` only when no explicit pin exists.

An invalid explicit override or locator is an error. A stale editable/global `sst_falsifier` installation cannot override the pin.

Pytest uses the same resolver through `conftest.py`, so framework selection is already fixed during test collection.

## Instance-local Python launchers

For custom helper modules/scripts use:

```bat
run_python.cmd -m my_package.tool --arg value
```

or:

```bat
run_python.cmd tools\helper.py --arg value
```

`run_python.cmd` delegates to `run_python.py`, which loads the authoritative framework pin before executing the requested instance-local code. This avoids Windows `ModuleNotFoundError` failures from launching below `tools\` and prevents an unrelated installed framework from being selected.

## Instance run modes

```text
run_all.cmd SELFTEST
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd FULL
run_all.cmd CERTIFY
run_all.cmd REVEAL
run_all.cmd REVEAL_IF_ALLOWED
```

`REVEAL` is strict and raises on an ineligible or invalid reveal state. `REVEAL_IF_ALLOWED` is intended for unattended orchestration: when the frozen scientific reveal policy is not yet satisfied, it writes a machine-readable `REVEAL_DECISION.json`, preserves blindness and returns success to the orchestration layer.

Integrity failures are still blockers; they are not reclassified as ordinary policy withholding.

## Reveal integrity

Before a reveal can proceed, v1.0.6 verifies:

- the blind `GATE_LEDGER.json` self-hash;
- the `RUN_SUMMARY.json` -> gate-ledger SHA-256 binding;
- the `OUTPUT_MANIFEST.json` self-hash;
- exact equality between that manifest and the current blind output tree;
- the frozen protocol bundle identity;
- the preregistered gate/status reveal policy;
- the unresolved-gate policy;
- the nonced reveal and forbidden-term commitments during reveal execution.

A successful reveal writes `REVEAL_DECISION.json` **before** the final output manifest and `_REVEALED.zip` are generated, so the decision itself is packaged and hashed.

A new blind run purges stale reveal artifacts, including `POST_RUN_DISCUSSION.tex`, prior revealed output, and the previously published parent-folder PDF.

## Output policy

For an instance folder such as `A056-v0.2.0`:

```text
A056-v0.2.0/
└── <configured-name>_<configured-version>-outputs/

../<configured-name>_<configured-version>-outputs_BLIND.zip
../<configured-name>_<configured-version>-outputs_REVEALED.zip
../A056-v0.2.0_FALSIFIER_REPORT.pdf
```

The TeX report is rendered when `latexmk` or `pdflatex` is available. TeX auxiliary files stay in a temporary build directory. `REPORT_RENDER.json` records the render result.

## Replication semantics

Cross-source scientific replication cannot be inferred from labels alone. Evidence classes distinguish:

```text
synthetic_control
simulation
independent_source
experimental
```

Synthetic controls may validate implementation-control replication, but cannot close an independent scientific cross-source replication gate.

## Local framework validation

From the framework root:

```bat
run_all.cmd ALL
```

Backend-only:

```bat
run_all.cmd BACKENDS
```

DD32-only:

```bat
run_all.cmd DD32
```

Runtime outputs:

```text
build/BACKEND_SELFTEST.json
build/DD32_PARITY_SMOKE.json
```

## Release cleanliness

Canonical source archives exclude generated `.pyd`, `.dll`, `.exe`, `.lib`, `.exp`, `.obj`, `.pyc`, `__pycache__`, `.pytest_cache`, `.venv`, `build/` and output trees.

`MANIFEST_SHA256.txt` has one stable meaning: it contains only the SHA-256 of `PACKAGE_MANIFEST.json`.

## Legacy policy

Keep older templates/framework releases for reproduction of historical falsifiers, but do not use them for new work. New falsifiers use v1.0.6 until a later canonical freeze explicitly supersedes it.
