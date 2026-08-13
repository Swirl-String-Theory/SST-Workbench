---
name: RR compile followups
overview: "Vervolg: alleen indien batch/ladder runtime dat eist — wijzigingen in ridgerunner compile-repo (C), niet in SST campaign scripts."
todos:
  - id: trigger-criteria
    content: "Documenteer wanneer compile-repo wél open mag (LA storms, OpenMP regressie, CLI flags ontbreken)"
    status: pending
  - id: isolate-fix
    content: "Fixes alleen in c:/workspace/projects/ridgerunner; SST blijft consumers via bin/ copy"
    status: pending
  - id: tests-check
    content: "make check / Windows smoke op ridgerunner.exe na C-change; geen campaign out/ in compile repo"
    status: pending
dependsOn: fseries_batch_ladder_94660855
isProject: false
---

# Vervolg: ridgerunner compile-repo (C)

**Depends on:** ervaring uit [fseries_batch_ladder_94660855](fseries_batch_ladder_94660855.plan.md) campaigns. **Niet starten** tenzij phase-1/batch een native bug of ontbrekende flag aantoont.

## Goal

Phase 1 raakt de compile-repo niet. Dit plan is de placeholder als batch-runs structurele C-problemen raken (tsnnls/LA storms, threading, CLI).

## Approach

- Compile-only: [`c:/workspace/projects/ridgerunner`](c:\workspace\projects\ridgerunner)
- Geen ideal/fseries campaign artifacts in compile `out/`
- Na fix: rebuild → kopieer exe/dlls naar [`KnotPlot/ridgerunner/bin`](c:\workspace\projects\SST-Workbench\KnotPlot\ridgerunner\bin)
- SST scripts blijven de driver

## Verification

- Autotools/CMake tests in compile repo
- SST unit suite ongewijzigd groen (scripts)
