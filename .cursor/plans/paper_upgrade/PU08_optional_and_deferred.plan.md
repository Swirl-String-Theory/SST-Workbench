---
name: PU08 optional and deferred
todos:
  - id: t00
    content: "Decide optional A024/A025/A016: RUN or SKIPPED with rationale from primary-chain signal"
    status: pending
  - id: t01
    content: "If RUN: optional-paper-control basic campaigns + covariance gates"
    status: pending
  - id: t02
    content: "A036/A039/A040: enforce dependency_guard; campaigns only if A030 PASS/QUALIFIED"
    status: pending
  - id: t03
    content: "Epic close note: optional/deferred status table"
    status: pending
---
# PU08 — Optional controls + deferred phase-clock guards

Status: `PLANNED` · Priority: P2 · Risk: low · Depends on: [PU07](PU07_orchestrator_a038_a021.plan.md); deferred campaigns also need [PU06](PU06_phase_floquet_a030_a023_a031.plan.md) A030 PASS  
Epic: [PAPER_UPGRADE_EPIC.plan.md](PAPER_UPGRADE_EPIC.plan.md)

## Todos

- [ ] Decide optional A024/A025/A016: RUN or SKIPPED with rationale from primary-chain signal
- [ ] If RUN: optional-paper-control basic campaigns + covariance gates
- [ ] A036/A039/A040: enforce `dependency_guard`; campaigns only if A030 PASS/QUALIFIED
- [ ] Epic close note: optional/deferred status table

## Optional (do not block A038)

Paths under `_variants/optional-paper-control`:

- **A024** threaded-hole
- **A025** local-thread texture
- **A016** Helmholtz transport

Run **only if** the primary chain (PU04–PU07) produced interesting PASS/QUALIFIED signals.
They are independent covariance / transport controls; they cannot create a primary PASS.
If RUN: same PU01b resume/heartbeat contract as other families (`/resume`, `heartbeat.log`).

Default if signal is weak/negative: mark `SKIPPED` with one-line rationale.

## Deferred guards (no campaign until A030)

\[
A030\neq\mathrm{PASS}
\quad\Longrightarrow\quad
\boxed{\text{geen A036/A039/A040 campaign}}
\]

- A036 / A039 / A040 patches are **dependency guards** only until
  `SST-GEOMETRIC-PHASE-1.0` exists.
- Selftests already ran in PU00 (`DEFERRED_UNTIL_A030_CERTIFIED` is PASS).
- After A030 PASS: may authorize migration / version bump per contract
  `NO_VERSION_BUMP_UNTIL_A030_SST-GEOMETRIC-PHASE-1.0_PASS` — campaigns still require an
  explicit go from the user.

## Out of scope forever for this epic

A011, A012, A013, A014, A015, A017, A018, A020, A032, A041, A042.

## Done criteria

- Status table written (RUN / SKIPPED / BLOCKED) for A024, A025, A016, A036, A039, A040.
- Epic todos `t08` and remaining epic checkboxes closable or explicitly deferred.

## Next

Close [PAPER_UPGRADE_EPIC.plan.md](PAPER_UPGRADE_EPIC.plan.md) or open a follow-up epic for
extended/full campaigns and post-A030 phase-clock families.
