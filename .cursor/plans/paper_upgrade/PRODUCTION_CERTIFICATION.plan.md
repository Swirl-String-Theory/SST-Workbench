---
name: PRODUCTION CERTIFICATION PATCHSET
todos:
  - id: pc00
    content: "PC00 SST-SCIENTIFIC-CERTIFICATE-1.0 + promotable()"
    status: completed
  - id: pc01
    content: "PC01 D006-v0.4.1 certificate/numeric regression cases"
    status: pending
  - id: pc02
    content: "PC02 A037-v0.3.1 convergence-qualified symmetry selection"
    status: pending
  - id: pc03
    content: "PC03 A034-v0.2.1 production constrained-admissibility"
    status: pending
  - id: pc04
    content: "PC04 A038-v0.4.1 promotion firewall"
    status: pending
  - id: pc05
    content: "PC05 optional provenance ledger"
    status: pending
---
# Production-certification patchset (post first-campaign)

Status: `PLANNED` · Version: 1.0 · Baseline: 2026-09-08  
Parent: [PAPER_UPGRADE_EPIC.plan.md](PAPER_UPGRADE_EPIC.plan.md)  
Report: [TOTAL_REPORT_2026-09-08.md](TOTAL_REPORT_2026-09-08.md)

## Intent

**Do not add more physics yet.** The first campaign showed the next patch must be a
**production-certification** patch: make green selftest, numerically valid run, and
scientific PASS three explicitly different states.

\[
\boxed{
\text{PU02b hardening}
\rightarrow
\text{A037 v0.3.1 Numerical Qualification}
\rightarrow
\text{A034 v0.2.1 Production Admissibility}
\rightarrow
\text{A038 v0.4.1 Promotion Firewall}
}
\]

Plus D006 regression fixtures that encode what the first run revealed.

## Patch table

| Patch | Base → Target | Pri | Role |
|-------|---------------|----:|------|
| [PC00](PC00_certificate_contract.plan.md) | shared `paper_upgrade` → **certificate-1.0** | P0 | SELFTEST ≠ CAMPAIGN; generic `promotable()` |
| [PC01](PC01_d006_regression.plan.md) | D006 **v0.4.0 → v0.4.1** | P0 | regression: parity-perfect+CFL-fail; fake selftest; weak manifold |
| [PC02](PC02_a037_v031.plan.md) | A037 **v0.3.0 → v0.3.1** | P0 | temporal/spatial qual → then χ_ij; split mirror vs physical |
| [PC03](PC03_a034_v021.plan.md) | A034 **v0.2.0 → v0.2.1** | P0 | keep dynamic FAIL; add constrained-energy branch + richer labels |
| [PC04](PC04_a038_v041.plan.md) | A038 **v0.4.0 → v0.4.1** | P0 | strict firewall; `BLOCKED_UPSTREAM_*` ≠ `FAIL_TREFOIL` |
| [PC05](PC05_provenance_ledger.plan.md) | optional repo-wide | P2 | provenance DAG / stage ledger |
| C006 | v0.2.0 → v0.2.1 | P1 | cert/provenance compatibility only |
| A029/A030 | **no bump** | — | wait for real A034/A037 CAMPAIGN certs |

> **Version note:** proposal text said D006 v0.3.0→v0.3.1; live workbench tip is
> `D006-v0.4.0`, so the target is **v0.4.1**.

## Three states (invariant)

| State | Meaning | May promote? |
|-------|---------|--------------|
| `PIPELINE_PASS` / SELFTEST | wiring + gate selftest | **no** |
| Numerically qualified | temporal/spatial/mesh gates PASS | necessary, not sufficient |
| Scientific CAMPAIGN `PASS` | paper observable assessed | **only if** `promotable(cert)` |

## Rerun order (after patches land)

1. `D006 → A037 → A034 → A038 preflight`
2. Only if both A037 and A034 emit promotable CAMPAIGN certs:
   `A029 → A035/A008 → A030 → A023/A031 → A038`

## Supersedes

Earlier drafts [PU04b](PU04b_a037_numerics_ladder.plan.md) / [PU04c](PU04c_a037_paper_2505.plan.md) /
[PU04d](PU04d_a034_dual_branch.plan.md) are absorbed into PC02/PC03.
PU02b v1 (fields + consumer reject) is **DONE**; remaining contract work is **PC00**.

## Todos

- [x] PC00 certificate contract
- [ ] PC01 D006-v0.4.1 regressions
- [ ] PC02 A037-v0.3.1
- [ ] PC03 A034-v0.2.1
- [ ] PC04 A038-v0.4.1
- [ ] PC05 optional provenance ledger
