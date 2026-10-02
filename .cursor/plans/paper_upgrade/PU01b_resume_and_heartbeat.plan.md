---
name: PU01b resume and heartbeat
todos:
  - id: t00
    content: "Shared helpers: run_state.json schema + heartbeat logger (07_scripts or paper_upgrade/_common)"
    status: completed
  - id: t01
    content: "Stage wrapper: skip completed stages on resume; mark .done on success"
    status: completed
  - id: t02
    content: "Wire all 18 patched families (stable OUT dir + /resume or SST_RESUME=1)"
    status: completed
  - id: t03
    content: "Heartbeat: stage START/END + periodic alive lines to heartbeat.log"
    status: completed
  - id: t04
    content: "Tests for resume skip, forced re-run, and heartbeat file format"
    status: completed
  - id: t05
    content: "Done-criteria: smoke resume mid-chain on one multi-stage family (e.g. A038)"
    status: completed
---
# PU01b — Resume-able falsifiers + heartbeat logging

Status: `DONE` · Priority: P0 · Risk: medium · Depends on: [PU01](PU01_run_all_selftest_hook.plan.md)  
Epic: [PAPER_UPGRADE_EPIC.plan.md](PAPER_UPGRADE_EPIC.plan.md)  
Blocks: [PU02](PU02_certificate_adapters.plan.md)

## Todos

Progress tracker — checkboxes include completed work so status is obvious at a glance.

- [x] Shared helpers: `run_state.json` schema + heartbeat logger
- [x] Stage wrapper: skip completed stages on resume; mark `.done` on success
- [x] Wire all 18 patched families (stable OUT dir + `/resume` or `SST_RESUME=1`)
- [x] Heartbeat: stage START/END + periodic alive lines to `heartbeat.log`
- [x] Tests for resume skip, forced re-run, and heartbeat file format
- [x] Done-criteria: smoke resume mid-chain on one multi-stage family (e.g. A038)

**Closed 2026-09-08:**
- `07_scripts/paper_upgrade_runtime.py` (+ `paper_upgrade_stage.cmd`, tests)
- 18/18 `run_all.cmd` with PU01b bootstrap + stage wraps where `call run_*.cmd`
- Mid-chain resume smoke PASS (`event=SKIP` then continue); D006 writes `heartbeat.log` / `run_state.json`

## Next

[PU02_certificate_adapters.plan.md](PU02_certificate_adapters.plan.md)


## Goal

Every patched falsifier campaign must be **interrupt-safe** and **observable while running**:

1. **Resume-able** — re-invoking `run_all` (or the family entrypoint) continues from the last
   successfully completed stage instead of restarting from scratch.
2. **Heartbeat logging** — a live log proves the process is alive during long stages
   (native builds, panels, RPO, long dynamics).

Today most families have neither: e.g. A037 stamps a new `outputs\basic_%STAMP%` every run,
and A038’s stage cmds always re-run. There is no shared `resume`/`heartbeat` helper in
`07_scripts` or templates.

## Design (canonical)

### Output layout under `outputs/<tier>/` (or family ROOTOUT tier)

```text
outputs/<tier>/
  run_state.json          # stages[], status, started_at, updated_at, pid optional
  heartbeat.log           # append-only; human + machine scrapeable
  stages/
    <stage_id>.done       # marker written only after stage exit 0
    <stage_id>.log        # optional per-stage stdout capture
  paper_upgrade/          # certificates (PU02)
  ... existing artifacts ...
```

### `run_state.json` (minimal schema)

```json
{
  "family": "A038",
  "tier": "basic",
  "status": "RUNNING",
  "resume": true,
  "stages": [
    {"id": "00_setup", "status": "DONE", "ended_at": "..."},
    {"id": "10_prepare", "status": "DONE", "ended_at": "..."},
    {"id": "40_long", "status": "RUNNING", "started_at": "..."}
  ],
  "updated_at": "..."
}
```

### Entry points

- Prefer **stable OUT** for resumable runs: `outputs\basic` (or explicit `%OUT%`), not a fresh timestamp each time.
- Timestamped dirs remain allowed for throwaway/debug runs via `/fresh` or `SST_FRESH=1`.
- Resume flags: `run_all.cmd /resume` and/or `set SST_RESUME=1`.
- Force redo one stage: `SST_FORCE_STAGE=40_long` (deletes that `.done` + later dependents if declared).

### Stage wrapper (shared)

Pseudo-contract for `07_scripts/paper_upgrade_stage.cmd` (or Python equivalent):

```bat
call paper_upgrade_stage.cmd <stage_id> <command...>
```

Behavior:

1. Heartbeat line: `HEARTBEAT family=… stage=… event=START ts=…`
2. If resume and `stages\<id>.done` exists → log `SKIP` and return 0.
3. Else run command; on success write `.done` and update `run_state.json`; on failure set
   `status=FAILED`, heartbeat `event=FAIL`, exit non-zero.
4. Long Python stages additionally start a heartbeat thread/timer (default **60s**) writing
   `event=ALIVE detail=…` until the stage finishes.

### Heartbeat line format (one line, scrapeable)

```text
YYYY-MM-DDTHH:MM:SSZ HEARTBEAT family=A038 tier=basic stage=40_long event=ALIVE elapsed_s=3600
```

Events: `START` | `ALIVE` | `SKIP` | `DONE` | `FAIL`.

Also echo the same line to console so IDE/terminal sessions show liveness.

## Per-family wiring

Apply to all 18 patched dirs (same set as PU00). Stage IDs should map to existing steps:

| Pattern | Stage IDs |
|---------|-----------|
| Multi `run_NN_*.cmd` (A038, A037, …) | `00_setup`, `01_build`, … matching script names |
| basic→extended chains (A021, A030) | `basic`, `extended` (resume mid-chain) |
| C006 presets | `deps`, `build`, `test`, `science_quick` |
| D006 | `selftest`, `demo`/`audit` as applicable |
| Single-campaign families | at least `selftest`, `campaign`, `paper_upgrade_cert` |

Certificate emit/consume stages (PU02) are also resume markers: do not re-emit if cert
unchanged unless `SST_FORCE_STAGE=paper_upgrade_cert`.

## Tests

- Unit: given a fake `.done`, wrapper SKIPs; without marker, runs and creates `.done`.
- Unit: heartbeat file receives START + at least one ALIVE under a short interval in test mode
  (`SST_HEARTBEAT_SEC=1`).
- Integration smoke: A038 (or smallest multi-stage family) — complete through stage N, kill,
  `/resume`, assert stages ≤ N skipped and N+1 runs.

## Out of scope

- Distributed/queue job systems.
- Changing scientific thresholds or blind/reveal policy.
- Making **unpatched** families (A011, …) resume-able in this epic.

## Done criteria

- Shared helper(s) land under `07_scripts/` (preferred) with tests.
- All 18 patched `run_all.cmd` (and D006’s new one) document `/resume` and write
  `heartbeat.log` + `run_state.json` under their OUT tier.
- Mid-chain resume smoke recorded in the PU01b log / notes.
- Epic hard rule “campaigns must be resume-able + heartbeat” is satisfiable for PU03+.

## Next

[PU02_certificate_adapters.plan.md](PU02_certificate_adapters.plan.md) — certificates live under the same resumable OUT tree.
