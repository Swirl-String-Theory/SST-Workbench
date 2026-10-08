# Canonical freeze — SST Falsifier Framework v1.0.6

**Status:** `CANONICAL_FROZEN`

v1.0.6 is the default framework for all new SST falsifiers. It consolidates the previous v1.0.4 production baseline and the three independently developed v1.0.5 hardening branches after review and regression testing.

## Canonical Workbench location

```text
06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.6
```

## Freeze rule

Never patch this directory in place. Any change to scientific/runtime code, gates, precision policy, launch/bootstrap logic, reveal semantics, reporting, provenance or packaging creates a new framework version.

The v1.0.5 candidate artifacts are retained only as development provenance; they are not canonical production baselines.

Target-machine Arc A770 evidence inherited from the unchanged backend implementation is retained under `validation/hardware/2026-10-07_arc-a770/`.
