# Canonical freeze — SST Falsifier Framework v1.0.4

**Status:** `CANONICAL_FROZEN`

This is the default framework for all new SST falsifiers. It supersedes the older blind/multi-library, C++/pybind and GPU/SYCL templates for new work. Historical packages remain unchanged for reproducibility.

## Rule

Never patch this directory in place. A change to code, gates, precision policy, templates, reports, packaging, source semantics or build logic creates a new framework version.

## Canonical Workbench location

```text
06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.4
```

Target-machine validation evidence is stored under `validation/hardware/2026-10-07_arc-a770/`.
