# SST Falsifier Framework v1.0.0

Canonical shared runtime for SST-Workbench falsification projects. This framework fuses the useful parts of the former:

- `SST_Blind_MultiLibrary_Falsifier_Template_v0.1.0`
- `SST_cpp_pybind_audit_template`
- `SST_GPU_SYCL_DPC_audit_template`

without turning them into a monolith. Scientific experiments remain thin instances; protocol, blindness, provenance, gate semantics, packaging, backend certification and reporting live here once.

## Core rule

A `PASS` is only valid when the gate that passed actually ran the preregistered source, implementation and precision class. Silent backend fallback is allowed for development only and can never satisfy a certification gate.

## Recommended Workbench location

```text
SST-Workbench/
└── 04_tools/
    └── D_proof/
        └── SST_Falsifier_Framework_v1.0.0/
```

Scientific instances remain under `01_research/A_falsifiers/...`.

## Profiles

- `minimal`: Python FP64/reference only.
- `cpu`: Python reference + strict C++/pybind11 certification.
- `gpu`: Python reference + strict C++ certification + SYCL screening/parity.
- `multilibrary_gpu`: same backend ladder plus independent multi-source discovery/confirmation contract.

## Quick start

```bat
run_00_setup.cmd
run_01_selftest.cmd
python tools\new_falsifier.py A056 my_falsifier C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A056_my_falsifier\A056-v0.1.0 --profile multilibrary_gpu --version v0.1.0
```

Then edit the generated scientific contract and `report/FALSIFIER_REPORT.tex`. Before any target-bearing scientific values are inspected:

```bat
run_all.cmd FREEZE
```

A frozen protocol includes hashes of the machine-readable science/source/gate contracts **and the human-readable LaTeX report**. `CERTIFY` refuses a changed or incomplete protocol.

## Run modes

```text
run_all.cmd SELFTEST
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd FULL
run_all.cmd CERTIFY
run_all.cmd REVEAL
```

The instance-local `run_all.cmd` calls `run_instance.py`, which loads this framework through `SST_FALSIFIER_FRAMEWORK_ROOT` or the standard Workbench location.

## Output policy

For `<Name>_vX.Y.Z`:

```text
./<Name>_vX.Y.Z-outputs/
../<Name>_vX.Y.Z-outputs_BLIND.zip
../<Name>_vX.Y.Z-outputs_REVEALED.zip
```

Release ZIPs are deterministic and source-package checks reject `.pyd`, `.dll`, `.exe`, `.lib`, `.exp`, `.obj`, `.pyc`, `__pycache__`, `.pytest_cache`, `build/` and prior output trees.

## Scientific report contract

Every generated falsifier contains `report/FALSIFIER_REPORT.tex`. It is not optional documentation: it is part of the preregistration bundle. It must state, before certification:

1. research question and objective;
2. null and alternative hypotheses;
3. admissible assumptions and domain;
4. symbols, units and dimensional checks;
5. exact equations and observables;
6. algorithmic steps mapping equations to code;
7. source and independence contract;
8. gate DAG and pass/fail semantics;
9. numerical convergence/error budget;
10. backend authority and parity tolerances;
11. blindness/reveal protocol;
12. statistical/null model and multiplicity handling;
13. results and provenance generated after execution.

See `docs/REPORT_CONTRACT.md`.

## Reveal safety

`REVEAL` is phase-separated from computation: it does not rerun the experiment. The default policy requires a previous FULL or CERTIFY blind run, a terminal PASS/FAIL discovery gate G3, no UNRESOLVED blind gates, and valid nonced commitments.
