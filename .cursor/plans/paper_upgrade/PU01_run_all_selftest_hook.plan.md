---
name: PU01 run_all selftest hook
todos:
  - id: t00
    content: "Insert call run_paper_upgrade.cmd early in every patched run_all.cmd"
    status: completed
  - id: t01
    content: "Add minimal D006 run_all.cmd (selftest + existing demo/audit)"
    status: completed
  - id: t02
    content: "Smoke: one producer + one consumer run_all aborts if selftest forced FAIL"
    status: completed
  - id: t03
    content: "Done-criteria: 17 existing run_alls + D006 hook verified"
    status: completed
---
# PU01 — Hook `run_paper_upgrade` into `run_all`

Status: `DONE` · Priority: P0 · Risk: low · Depends on: [PU00](PU00_selftests.plan.md)  
Epic: [PAPER_UPGRADE_EPIC.plan.md](PAPER_UPGRADE_EPIC.plan.md)

## Todos

Progress tracker — checkboxes include completed work so status is obvious at a glance.

- [x] Insert `call run_paper_upgrade.cmd` early in every patched `run_all.cmd`
- [x] Add minimal D006 `run_all.cmd` (selftest + existing demo/audit)
- [x] Smoke: one producer + one consumer `run_all` aborts if selftest forced FAIL
- [x] Done-criteria: 17 existing run_alls + D006 hook verified

**Closed 2026-09-08:** 18 `run_all.cmd` files hook `run_paper_upgrade`; A034/A021 abort with rc=1 on forced FAIL; D006 `run_all` demo+audit PASS.

## Next

[PU01b_resume_and_heartbeat.plan.md](PU01b_resume_and_heartbeat.plan.md)


## Goal

Ensure every scientific entrypoint fails fast if the paper-upgrade gate is broken.
This does **not** yet emit certificates from campaign physics (that is PU02).

## Pattern

After `cd /d "%~dp0"` (or equivalent):

```bat
echo [paper-upgrade] gate selftest
call run_paper_upgrade.cmd || exit /b 1
```

Families with `run_all.cmd` today: C006, A008, A016, A021, A023, A024, A025, A029,
A030, A031, A034, A035, A036, A037, A038, A039, A040.

D006 currently has **no** `run_all.cmd` — add a minimal one that only runs
`run_paper_upgrade.cmd` then the existing cheap demo/audit path from its README.

## Out of scope

- Certificate emission / consumption (PU02).
- Changing blind/reveal policy.
- Scientific campaign execution.

## Done criteria

- Grep/`rg` over the 18 dirs shows `run_paper_upgrade` referenced from `run_all.cmd`.
- D006 has a `run_all.cmd`.
- Documented smoke check: with a temporary broken selftest, `run_all` exits non-zero
  before campaign stages (then restore).

## Next

[PU01b_resume_and_heartbeat.plan.md](PU01b_resume_and_heartbeat.plan.md)
