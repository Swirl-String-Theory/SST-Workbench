# A054 v0.2.0-r3 — progress + checkpoint/resume hotfix

Scientific configuration is unchanged from v0.2.0/r1/r2.

## Added

- Atomic checkpoint after every completed `(anonymous_id, sector, N)` certification unit.
- Checkpoints are bound to exact config SHA-256, blind manifest SHA-256, solver SHA-256 and backend name.
- `--resume` reuses only provenance-compatible checkpoints.
- `--fresh` explicitly discards checkpoints and final certification outputs before recomputation.
- `PROGRESS.json` heartbeat is updated every ~15 s while a heavy unit is running.
- Console progress includes candidate index, circulation sector, N, current phase, completed units and ETA.
- A run lock prevents two certification processes from writing to the same campaign concurrently.
- `run_resume_full.cmd [campaign-dir]`; without a path it selects the newest `full_*` campaign.
- `run_restart_full_fresh.cmd <campaign-dir>` for an explicit from-zero rerun.

## Important limitation

A v0.2.0-r2 process that was already running before this hotfix cannot be retroactively checkpointed because r2 keeps completed certification units only in process memory until the full nested loop finishes. Let an active r2 run finish if possible. If it is interrupted, r3 can reuse the prepared campaign but must start certification from unit 0 unless r3 checkpoints already exist.

## Blindness

Checkpoints contain only anonymous IDs and blind numerical results. `_private` remains inaccessible to the isolated runner. Checkpoint files and the transient run lock are excluded from distribution archives.
