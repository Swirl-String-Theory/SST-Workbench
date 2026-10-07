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
