# SST Falsifier Framework v1.0.9 — CANONICAL_FROZEN

**Date:** 2026-10-17  
**Canonical install:** `SST-Workbench/06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.9`  
**Parent:** v1.0.8 `LOCAL_VALIDATED_CANDIDATE` (v1.0.7 retained as historical canonical ancestor).

This is the production source baseline for **new** SST falsifier instances after target-machine validation. Existing frozen falsifier campaigns must remain pinned to the framework they originally used.

## New in v1.0.9

- Preserves v1.0.8 **run-ID + no-overwrite** behavior: unique BLIND/REVEALED ZIPs/PDFs and archived previous output trees, without changing the working output path.
- Fixes report circularity with a **create-once science-evidence SHA**; the final output-tree manifest remains separate and verifiable.
- Adds a supplementary **cross-platform diagnostic** fingerprint for line-ending normalization; raw byte-exact frozen protocol hash remains authoritative.
- Fixes long gate-ledger PDF tables and wraps backend/source display JSON for paper-size layout.
- Adds instance `run_all.cmd REPORT_ONLY` for unique PDF rerenders that never replace old reports or mutate historical scientific results.
- Adds optional `SST_LATEX_ENGINE` and `report.pdf_engine` selection for LaTeX engines.
- Does **not** alter scientific gates, thresholds, source-admissibility rules, C++/SYCL/DD32 kernels or backend authority.

## Install and verify on Windows

Unzip into the directory above, beside your older framework versions; do not overwrite v1.0.7 or v1.0.8.

```bat
cd /d C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.9
run_all.cmd ALL
```

For a generated scientific instance:

```bat
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd REPORT_ONLY
```

`REPORT_ONLY` operates on an existing current run and requires an intact `OUTPUT_MANIFEST.json` and `SCIENCE_EVIDENCE_MANIFEST.json`. Repeated invocation creates distinct PDFs instead of overwriting.

For CPU/SYCL screening and full Windows hardware parity also retain `build/BACKEND_SELFTEST.json`. DD32 is still **SCREENING_ONLY**, not native IEEE FP64. The local framework unit tests do not qualify SST physical claims.

See `docs/V1.0.9_CONSOLIDATION.md`, `CANONICAL_FREEZE.md`, `VALIDATION.md` and `docs/EXPORT_RETENTION_POLICY.md`.
