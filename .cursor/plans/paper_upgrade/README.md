# Paper-upgrade planning set

Two phases:

1. **First campaign (DONE through PU04 + PU02b v1)** — selftests, wiring, resume, infra, A037/A034 basic.
2. **Production-certification patchset (ACTIVE)** — no new physics; harden certificates + version bumps.

## Reading order (now)

1. [TOTAL_REPORT_2026-09-08.md](TOTAL_REPORT_2026-09-08.md) — corrected labels from first run  
2. [PRODUCTION_CERTIFICATION.plan.md](PRODUCTION_CERTIFICATION.plan.md) — **start here for follow-up**  
3. [PAPER_UPGRADE_EPIC.plan.md](PAPER_UPGRADE_EPIC.plan.md) — original epic invariants  

## Production-certification sub-plans (active)

| ID | Title | Status | Pri |
|----|-------|--------|----:|
| [PC00](PC00_certificate_contract.plan.md) | `SST-SCIENTIFIC-CERTIFICATE-1.0` + `promotable()` | `DONE` | P0 |
| [PC01](PC01_d006_regression.plan.md) | D006 v0.4.0 → **v0.4.1** regressions | `PLANNED` | P0 |
| [PC02](PC02_a037_v031.plan.md) | A037 → **v0.3.1** convergence-qualified symmetry | `PLANNED` | P0 |
| [PC03](PC03_a034_v021.plan.md) | A034 → **v0.2.1** production constrained-admissibility | `PLANNED` | P0 |
| [PC04](PC04_a038_v041.plan.md) | A038 → **v0.4.1** promotion firewall | `PLANNED` | P0 |
| [PC05](PC05_provenance_ledger.plan.md) | Optional provenance ledger | `PLANNED` | P2 |

\[
\boxed{
\text{PC00}
\rightarrow
\text{A037 v0.3.1}
\rightarrow
\text{A034 v0.2.1}
\rightarrow
\text{A038 v0.4.1}
}
\]

(+ D006 v0.4.1 regressions in parallel after PC00)

**Resume here:** [PC01_d006_regression.plan.md](PC01_d006_regression.plan.md) (then PC02 A037 v0.3.1). PC00 `DONE`.

## First-campaign sub-plans (archive)

| ID | Title | Status |
|----|-------|--------|
| [PU00](PU00_selftests.plan.md) | 18× selftests | `DONE` |
| [PU01](PU01_run_all_selftest_hook.plan.md) | run_all hooks | `DONE` |
| [PU01b](PU01b_resume_and_heartbeat.plan.md) | resume + heartbeat | `DONE` |
| [PU02](PU02_certificate_adapters.plan.md) | cert adapters | `DONE` |
| [PU02b](PU02b_certificate_semantics.plan.md) | cert semantics v1 | `DONE` → continued by PC00 |
| [PU03](PU03_infra_d006_c006.plan.md) | D006+C006 | `DONE` |
| [PU04](PU04_primary_gates_a037_a034.plan.md) | first A037/A034 basic | `DONE` |
| PU04b/c/d | drafts | **superseded** by PC02/PC03 |
| [PU05](PU05_modal_a029_a035_a008.plan.md)–[PU08](PU08_optional_and_deferred.plan.md) | downstream | `BLOCKED` until promotable CAMPAIGN certs |

## Corrected first-run labels

| Family | Label |
|--------|-------|
| A037 | `INVALID_NUMERICS / NOT_YET_TESTED_2505` |
| A034 | `OLD_QHP_DYNAMIC_GATE_FAIL / NOT_YET_TESTED_1806` |

## Hard rules

1. Selftests before campaigns.
2. `PIPELINE_PASS` ≠ scientific PASS ≠ numerically qualified.
3. Promote only if shared `promotable(cert)` is true (PC00).
4. A038 must report `BLOCKED_UPSTREAM_*`, never collapse numeric blocks into `FAIL_TREFOIL`.
5. Keep A034 dynamic FAIL archived; energy branch is additive.
6. A029/A030: **no version bump** until real A034/A037 CAMPAIGN certs exist.
7. Basic/quick first; no extended unless requested after basic PASS.
