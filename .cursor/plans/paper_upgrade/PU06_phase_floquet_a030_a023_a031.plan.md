---
name: PU06 phase floquet A030 A023 A031
todos:
  - id: t00
    content: "A030 v0.2.0 basic geometric-phase grid/loop; emit SST-GEOMETRIC-PHASE-1.0"
    status: pending
  - id: t01
    content: "A023 v0.5.0 basic RPO/Floquet discovery after A034 + C006"
    status: pending
  - id: t02
    content: "A031 v0.2.0 basic adaptive-period / multiple-shooting certification"
    status: pending
  - id: t03
    content: "Record A030 cert path for PU08 deferred guards"
    status: pending
---
# PU06 — Phase / monodromy: A030 → A023 → A031

Status: `PLANNED` · Priority: P1 · Risk: high · Depends on: [PU05](PU05_modal_a029_a035_a008.plan.md), [PU03](PU03_infra_d006_c006.plan.md)  
Epic: [PAPER_UPGRADE_EPIC.plan.md](PAPER_UPGRADE_EPIC.plan.md)

## Todos

- [ ] A030 v0.2.0 basic geometric-phase grid/loop; emit `SST-GEOMETRIC-PHASE-1.0`
- [ ] A023 v0.5.0 basic RPO/Floquet discovery after A034 + C006
- [ ] A031 v0.2.0 basic adaptive-period / multiple-shooting certification
- [ ] Record A030 cert path for PU08 deferred guards

## Goal

Produce geometric-phase and Floquet-parity evidence in the preferred order
**A030 → A023 → A031** (A023 discovery before A031 strict certification).

## Families

### A030 v0.2.0

- Needs parameter-space grid/loop: \(\mathcal A_i\), \(\mathcal F_{ij}\), \(\gamma[C]\).
- Old phase-delay-only output is **not** enough.
- Certificate unlocks A036 / A039 / A040 (PU08 deferred).

### A023 v0.5.0

- Broad RPO candidate → \(M(T)\) → \(\mu_i\).
- Requires A034 admissibility + C006-qualified infra.
- Mirror conjugacy: \(\mathrm{spec}\,M_K(T)\stackrel{?}{\sim}\mathrm{spec}\,M_{PK}(T)\).

### A031 v0.2.0

- Stricter adaptive-period / multiple-shooting certification of the same Floquet contract.
- Period adaptation must not absorb mirror-parity failure.

## Configs

Basic / panel-basic only in this sub-plan. Use `/resume` for long RPO/Floquet stages;
watch `heartbeat.log` for `ALIVE` during `40_long`-class work where applicable.

## Done criteria

- A030 certificate path recorded (`SST_A030_CERT`).
- A023 then A031 basic panels complete with Floquet parity adapter results.
- Failures logged without promoting failed candidates.

## Next

[PU07_orchestrator_a038_a021.plan.md](PU07_orchestrator_a038_a021.plan.md)
