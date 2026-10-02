---
name: PU04 primary gates A037 A034
todos:
  - id: t00
    content: "A037 v0.3.0 run_all basic; emit SST-SYMMETRY-SELECTION-1.0"
    status: completed
  - id: t01
    content: "A034 v0.2.0 run_all basic on existing QHP geometry; emit SST-ADMISSIBILITY-1.0"
    status: completed
  - id: t02
    content: "Apply stop/go: FAIL ⇒ no downstream candidate promotion"
    status: completed
  - id: t03
    content: "Record certificate paths for A038/A021 consumers"
    status: completed
---
# PU04 — Primary gates: A037 → A034

Status: `DONE` · Priority: P0 · Risk: high · Depends on: [PU03](PU03_infra_d006_c006.plan.md)  
Epic: [PAPER_UPGRADE_EPIC.plan.md](PAPER_UPGRADE_EPIC.plan.md)

## Todos

Progress tracker — checkboxes include completed work so status is obvious at a glance.

- [x] A037 v0.3.0 `run_all` basic; emit `SST-SYMMETRY-SELECTION-1.0`
- [x] A034 v0.2.0 `run_all` basic on existing QHP geometry; emit `SST-ADMISSIBILITY-1.0`
- [x] Apply stop/go: FAIL ⇒ no downstream candidate promotion
- [x] Record certificate paths for A038/A021 consumers

**Closed 2026-09-08 — engineering OK; corrected science labels (v2):**

| Family | Engineering | Corrected label | Notes |
|--------|-------------|-----------------|-------|
| A037 | PASS | `INVALID_NUMERICS / NOT_YET_TESTED_2505` | 6/6 `INVALID_TRAJECTORY_TIMESTEP` (CFL~3–10). Mirror parity is code sanity, not physical detection. v0.2.0 analysis still running; Paper-2505 χ_ij **not executed**. |
| A034 | PASS | `OLD_QHP_DYNAMIC_GATE_FAIL / NOT_YET_TESTED_1806` | Real negative: 0 confirmed restoring on 588 candidates. Package still 0.1.3 / QHP-*-1.3; constrained \(g,H\) **not tested**. Synthetic certs unsafe. |

**Stop/go:** pause PU05+ — not because Paper-2505/1806 falsified SST, but because numerics invalid + old dynamic FAIL + production gates missing.

Logs: `A037.../outputs/_pu04_a037_run.log`, `A034.../outputs/_pu04_a034_run.log`  
Report: [TOTAL_REPORT_2026-09-08.md](TOTAL_REPORT_2026-09-08.md)

## Next

[PU02b_certificate_semantics.plan.md](PU02b_certificate_semantics.plan.md) (required before any further campaigns).
