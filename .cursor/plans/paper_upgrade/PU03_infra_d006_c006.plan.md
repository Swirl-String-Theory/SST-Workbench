---
name: PU03 infra D006 C006
todos:
  - id: t00
    content: "D006: run paper-upgrade path + numerical cert (no SST campaign); FAIL stops epic"
    status: completed
  - id: t01
    content: "C006: run_all.cmd quick after selftest hook; Floquet/workbench validation"
    status: completed
  - id: t02
    content: "Log outputs/audit paths; record PASS/FAIL"
    status: completed
  - id: t03
    content: "Done-criteria: D006 PASS and C006 quick PASS"
    status: completed
---
# PU03 — Scientific infra: D006 + C006

Status: `DONE` · Priority: P0 · Risk: medium · Depends on: [PU02](PU02_certificate_adapters.plan.md)  
Epic: [PAPER_UPGRADE_EPIC.plan.md](PAPER_UPGRADE_EPIC.plan.md)

## Todos

Progress tracker — checkboxes include completed work so status is obvious at a glance.

- [x] D006: run paper-upgrade path + numerical cert (no SST campaign); FAIL stops epic
- [x] C006: `run_all.cmd` quick after selftest hook; Floquet/workbench validation
- [x] Log outputs/audit paths; record PASS/FAIL
- [x] Done-criteria: D006 PASS and C006 quick PASS

**Closed 2026-09-08:**
- D006 `run_all` PASS (`outputs/basic/heartbeat.log`, synthetic audit NOT_FALSIFIED)
- C006 quick PASS — `audit_out_quick_20260908_175840/audit_summary.json` (9 tests + K0–K14)
- Fix: `cpp/native.cpp` `ssize_t` → `py::ssize_t` for MSVC build

## Next

[PU04_primary_gates_a037_a034.plan.md](PU04_primary_gates_a037_a034.plan.md)
