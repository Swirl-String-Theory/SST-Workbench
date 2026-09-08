---
name: PU02 certificate adapters
todos:
  - id: t00
    content: "Define canonical certificate path + env vars (A034/A037/A030)"
    status: completed
  - id: t01
    content: "Producer adapters: A037, A034, A030 synthetic emit (Floquet/modal follow-up)"
    status: completed
  - id: t02
    content: "Consumer hooks: A038 upstream_gate, A021 consume_a034, A036 guard"
    status: completed
  - id: t03
    content: "Wire post-campaign emit / pre-expensive-stage consume into run_all chains"
    status: completed
  - id: t04
    content: "Tests for adapters (test_paper_upgrade_certs.py)"
    status: completed
  - id: t05
    content: "Done-criteria: synthetic fixture end-to-end PASS; gaps documented"
    status: completed
---
# PU02 — Certificate adapters (producer / consumer)

Status: `DONE` · Priority: P0 · Risk: medium · Depends on: [PU01b](PU01b_resume_and_heartbeat.plan.md)  
Epic: [PAPER_UPGRADE_EPIC.plan.md](PAPER_UPGRADE_EPIC.plan.md)

## Todos

Progress tracker — checkboxes include completed work so status is obvious at a glance.

- [x] Define canonical certificate path + env vars (A034/A037/A030)
- [x] Producer adapters: A037, A034 (+ A030 helper); Floquet/modal emit deferred to campaign SPs
- [x] Consumer hooks: A038 `upstream_gate`, A021 `consume_a034`, A036 `dependency_guard`
- [x] Wire post-campaign emit / pre-expensive-stage consume into A034/A037/A021/A038 `run_all.cmd`
- [x] Tests: `07_scripts/test_paper_upgrade_certs.py`
- [x] Done-criteria: synthetic fixture end-to-end PASS; gaps in [PU02_GAPS.md](PU02_GAPS.md)

**Closed 2026-09-08:**
- `07_scripts/paper_upgrade_certs.py`
- A037 gate `_write` numpy JSON fix
- Synthetic certs prove pipeline; real \(g,H,C\)/\(\chi\) extraction still GAP (documented)

## Next

[PU03_infra_d006_c006.plan.md](PU03_infra_d006_c006.plan.md)
