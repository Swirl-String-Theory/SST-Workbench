---
name: PU07 orchestrator A038 A021
todos:
  - id: t00
    content: "A038 upstream_gate with A034+A037 (+ geometry/mesh) before expensive stages"
    status: pending
  - id: t01
    content: "A038 qualification/report/orchestration rerun; reuse provenance-clean artifacts where allowed"
    status: pending
  - id: t02
    content: "A021 consume_a034; revise verdict from existing confinement evidence"
    status: pending
  - id: t03
    content: "New A021 dynamics only for A034 candidates never dynamically tested"
    status: pending
---
# PU07 — Integrated decision: A038 → A021

Status: `PLANNED` · Priority: P0 · Risk: high · Depends on: [PU06](PU06_phase_floquet_a030_a023_a031.plan.md), [PU04](PU04_primary_gates_a037_a034.plan.md)  
Epic: [PAPER_UPGRADE_EPIC.plan.md](PAPER_UPGRADE_EPIC.plan.md)

## Todos

- [ ] A038 `upstream_gate` with A034+A037 (+ geometry/mesh) before expensive stages
- [ ] A038 qualification/report/orchestration rerun; reuse provenance-clean artifacts where allowed
- [ ] A021 `consume_a034`; revise verdict from existing confinement evidence
- [ ] New A021 dynamics only for A034 candidates never dynamically tested

## Goal

Treat A038 as orchestrator/certificate consumer and A021 as A034 consumer — not as
second full landscape solvers.

## A038 v0.4.0

Minimum certificates:

- \(G_{\mathrm{symmetry}}^{A037}\)
- \(G_{\mathrm{admissibility}}^{A034}\)

Extended chain may also consume results from A029, A030, A023/A031, A035 when present.

- `run_all.cmd` requires a **held-out trefoil atlas path**. If missing, mark this todo
  `BLOCKED` with the missing path named — do not invent atlas data.
- Prefer reusing provenance-clean numerical artifacts; **must** re-run qualification /
  report / orchestration so the new PASS status can exist.
- Stage chain is the primary resume smoke target (S10–S70); `/resume` must skip completed
  stages and continue heartbeat through remaining work.
- Do not start as the first expensive campaign of the epic (already enforced by deps).

## A021 v0.4.0

```text
A034 certificate → ingest
existing self-confinement evidence → revised verdict
```

- No second complete self-confinement landscape by default.
- New dynamics only when A034 points to a candidate A021 never dynamically tested.

## Done criteria

- A038 `downstream_authorized` decision logged (true/false + reasons).
- A021 accept/reject of A034 cert logged with revised verdict path.
- Blind/reveal zips updated if the family archive step runs.

## Next

[PU08_optional_and_deferred.plan.md](PU08_optional_and_deferred.plan.md)
