# Architecture

```text
scientific instance
  ├─ science_contract.json + FALSIFIER_REPORT.tex  (what is being tested)
  ├─ source_contract.json                           (what data may enter)
  ├─ gate_plan.json                                 (causal decision DAG)
  ├─ experiment/pipeline.py                         (experiment-specific science)
  └─ native/cpp/*                                   (experiment-specific native kernels)
             │
             ▼
SST Falsifier Framework
  ├─ immutable protocol / blindness / reveal
  ├─ provenance / deterministic packaging
  ├─ gate ledger + dependency enforcement
  ├─ source registry resolver
  ├─ Python reference backend
  ├─ shared pybind build machinery
  ├─ shared external SYCL worker machinery
  └─ report/provenance generators
```

## Trust boundary

The framework may provide development fallbacks, but `BackendResult.authority` controls what a gate may claim. `DEVELOPMENT` or `SCREENING_ONLY` cannot satisfy a `CERTIFICATION` requirement.

## Why native kernels stay instance-local

Scientific C++/SYCL formulas must remain inspectable beside the falsifier that uses them. The build/runtime machinery is shared; the experiment-specific kernel is not hidden inside a global framework binary. This preserves equation-to-code auditability while eliminating copied build scripts.
## Instance-local launcher path contract

Generated instances expose `run_python.cmd` as the canonical wrapper for custom Python entry points. The wrapper changes to the instance root and prepends that root to `PYTHONPATH` before invoking Python. Custom launchers should prefer `run_python.cmd -m package.module ...`. If a `tools/*.py` file is intentionally executable directly, it must insert `Path(__file__).resolve().parents[1]` into `sys.path` before importing sibling instance packages.


## Authoritative framework pin

`framework_bootstrap.py` is instance-local and runs before the shared framework is imported. Explicit environment override and generated locator are authoritative and fail closed when invalid. An arbitrary editable/global `sst_falsifier` import is never accepted in place of the pin.

## Reveal integrity boundary

Reveal policy is evaluated only after the blind gate ledger self-hash, run-summary ledger binding and exact blind output manifest have been verified. `REVEAL_IF_ALLOWED` may withhold reveal without treating a scientifically negative result as a runtime error; integrity failures remain explicit blockers.
