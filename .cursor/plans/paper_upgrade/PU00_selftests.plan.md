---
name: PU00 selftests
todos:
  - id: t00
    content: "pytest 07_scripts/test_paper_upgrade_gates.py → 18/18 PASS"
    status: completed
  - id: t01
    content: "Add 07_scripts/run_paper_upgrade_selftests.cmd (protocol order, stop on FAIL)"
    status: completed
  - id: t02
    content: "Run sequential selftests D006…A040; log PASS/FAIL per family"
    status: completed
  - id: t03
    content: "Done-criteria: 18/18 PASS; no campaign started"
    status: completed
---
# PU00 — Patch selftests (18×)

Status: `DONE` · Priority: P0 · Risk: low · Depends on: nothing  
Epic: [PAPER_UPGRADE_EPIC.plan.md](PAPER_UPGRADE_EPIC.plan.md)

## Todos

Progress tracker — checkboxes include completed work so status is obvious at a glance.

- [x] pytest `07_scripts/test_paper_upgrade_gates.py` → 18/18 PASS
- [x] Add `07_scripts/run_paper_upgrade_selftests.cmd` (protocol order, stop on FAIL)
- [x] Run sequential selftests D006…A040; log PASS/FAIL per family
- [x] Done-criteria: 18/18 PASS; no campaign started

**Closed 2026-09-08:** pytest 19 passed; sequential runner `18/18 PASS FAIL=0`.

## Next

[PU01_run_all_selftest_hook.plan.md](PU01_run_all_selftest_hook.plan.md)

## Goal

Cheap validation that every paper-upgrade patch is installed and `gate.py --selftest`
returns PASS on this machine. **100% PASS required** before any scientific campaign.

## Preconditions

- Working tree has the 18 patched version directories present.
- Python with numpy available for gate selftests.

## Protocol order

```text
D006 → C006
A037 → A034
A029 → A030
A023 → A031
A035 → A008
A038 → A021
A024 → A025 → A016   (optional families; selftest still required)
A036 → A039 → A040   (guards only; DEFERRED_UNTIL_A030_CERTIFIED is PASS)
```

In each directory:

```bat
run_paper_upgrade.cmd
```

Canonical paths are listed in [`07_scripts/test_paper_upgrade_gates.py`](../../07_scripts/test_paper_upgrade_gates.py) (`EXPECTED_GATES`).

## Steps

1. Run `pytest 07_scripts/test_paper_upgrade_gates.py`. On FAIL: fix missing path or gate bug; do not continue.
2. Add a thin sequential runner `07_scripts/run_paper_upgrade_selftests.cmd` that `cd`s into each family dir, calls `run_paper_upgrade.cmd`, echoes `[ID] PASS|FAIL`, exits non-zero on first failure.
3. Execute the runner; write a one-page log (stdout capture is enough) with 18 lines.
4. Confirm no `run_all.cmd` / campaign was started in this sub-plan.

## Done criteria

- Pytest: 18 parametrized cases PASS.
- Sequential cmd: 18/18 PASS (including optional + deferred guard selftests).
- Epic todo `t00` can be checked.

## Next

[PU01_run_all_selftest_hook.plan.md](PU01_run_all_selftest_hook.plan.md)
