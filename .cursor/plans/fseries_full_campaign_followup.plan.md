---
name: Fseries full campaign
overview: "Vervolg: operationele full-catalog RR-run van alle 78 fseries met -r150,300,600,900,1200 -t12 na groene phase-1 tests — monitoring, resume, triage failures."
todos:
  - id: preflight
    content: Dry-run discovery 78 stems; disk space check; multithread exe -t12 smoke op 3_1
    status: completed
  - id: launch-campaign
    content: Start run_catalog_batch.cmd --all-fseries -r150,300,600,900,1200 -t12; log + summary path
    status: in_progress
  - id: triage
    content: Triage failures uit batch_fseries_summary.json; resume zonder --force waar mogelijk
    status: pending
  - id: report
    content: Korte Rop-tabel per stem/N; open bugs doorzetten naar compile/parallel/catalog follow-ups
    status: pending
isProject: false
---

# Vervolg: full 78-knot fseries RR campaign

**Depends on:** [fseries_batch_ladder_94660855](fseries_batch_ladder_94660855.plan.md) geïmplementeerd + unit suite groen.

## Goal

Phase 1 gebruikt unittests als implementatie-gate. Dit plan is de **operationele** campagne:

```bat
run_catalog_batch.cmd --all-fseries -r150,300,600,900,1200 -t12
```

## Approach

- Preflight: `--dry-run`, smoke `3_1` op 150→300.
- Lange run; resume bij interrupt.
- Failures niet stilzwijgend: summary + per-stem logs; herrun subset via `--stems`.
- Resultaten onder `KnotPlot/ridgerunner/out/<stem>/t12/` + `out/batch_fseries_summary.json`.

## Verification

- Summary: 78 entries, counts ok/failed/skipped
- Steekproef metrics N150/N300/N1200 voor bekende knopen (bijv. `3_1`)
