# E011 PKLSA Cross-Falsifier Campaign v0.1.0

This package orchestrates a **fresh common-carrier requalification campaign**. It prevents accidental reuse of scientific results produced on legacy knot/link geometries.

Recommended install path:

```text
C:\workspace\projects\SST-Workbench\01_research\E_pipelines\E011_pklsa_cross_falsifier_campaign\E011-v0.1.0\
```

Inspect eligibility first:

```bat
run_all_cross_falsifier.cmd PLAN C:\workspace\projects\SST-Workbench
```

Then run `BASIC`, `FULL`, or `CERTIFY`.

Old packages are **not** automatically run. A package participates only when it contains an explicit `cross_falsifier_contract.json` satisfying the current PKLSA common-carrier contract.
