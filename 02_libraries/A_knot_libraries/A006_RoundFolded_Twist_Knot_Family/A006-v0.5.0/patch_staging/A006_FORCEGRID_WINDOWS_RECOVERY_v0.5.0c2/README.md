# A006 v0.5.0c2 — Windows CRLF-aware ForceGrid recovery

**Target:** the current A006 v0.5.0 / v0.5.0a project with an interrupted v0.5.0c/v0.5.0c1 ForceGrid installation. This is a *recovery hotfix*, not a new geometry or research protocol release.

## Root cause reproduced

v0.5.0c saves a generated KnotPlot script using `Path.write_text()` (Windows writes **CRLF** line endings) but stores `sha256(s.encode())` in `PLAN.json` where `s` uses **LF**. The v0.5.0c1 repair compared `sha256(file raw bytes)` against that stored digest, and therefore rejected valid, identical Windows scripts with `Existing planned script absent/modified`, then restored `run_all.cmd` and `knotplotrc.kps`. In that failure state, v0.5.0c1 could leave a `patch_backups/v050c1_RUNNER_RECOVERY` directory without a completed `RECOVERY.json`.

v0.5.0c2 verifies *canonical LF UTF-8 script content*, rather than Windows raw-byte hash, and uses its own `patch_backups/v050c2_WINDOWS_RECOVERY` folder. Existing v0.5.0c1 backups are **not overwritten or deleted**. Actual script modifications, missing planned scripts, invalid seed hashes, and alias collisions still cause refusal.

## Install from the existing project root

Extract the archive such that the folder is:

`patch_staging\A006_FORCEGRID_WINDOWS_RECOVERY_v0.5.0c2\`

Then:

```bat
py -3 patch_staging\A006_FORCEGRID_WINDOWS_RECOVERY_v0.5.0c2\repair.py --base . --check
py -3 patch_staging\A006_FORCEGRID_WINDOWS_RECOVERY_v0.5.0c2\repair.py --base . --apply
run_all.cmd FORCEGRID TEST
run_all.cmd FORCEGRID PLAN
run_all.cmd FORCEGRID BUILD
```

Because this is a recovery, **do not re-run the older c/c1 installers** and do not delete `Output/qualification_v050c` or existing backups. If `--check` reports something other than the recorded problem, review it instead of attempting to force an install.

`FORCEQUAL` routing is restored if `tools\force_qualification_v050b.py` is already present. `FORCEGRID` includes all 14 arms; an independent v0.5.0b installation is not required for those.

## Safety and evidence

- No changes to `Output/v050/geometry`, knot seeds, the 336 v0.5.0 campaigns, or prior KnotPlot checkpoint files.
- When an existing ForceGrid `PLAN.json` is present, **no regenerated plan or scripts**: validate seed SHA-256, arm count, and every normalized script SHA-256. All fourteen existing scripts retain their original bytes.
- If ForceGrid planning is truly absent and there is no orphan output folder, the original v0.5.0c builder prepares the fourteen scripts and matching plan.
- Transactional modifications of `run_all.cmd` and `knotplotrc.kps` with guarded rollback; no automatic deletion of a prior failed recovery backup.
- Neither `--check` nor `--apply` runs KnotPlot GUI dynamics. `BUILD` prepares files only. New runs must still be executed in KnotPlot.
- Static/integration testing uses a bundled fixture and simulates Windows CRLF. Actual Windows `cmd.exe` and KnotPlot GUI execution **have not** been tested here.

## Self-test and rollback

```bat
py -3 patch_staging\A006_FORCEGRID_WINDOWS_RECOVERY_v0.5.0c2\tests\test_windows_recovery.py
```

Requires NumPy. Tests are isolated in temporary directories and do **not** operate on your actual workbench directory.

After a successful `--apply`, guarded rollback of `run_all.cmd` and `knotplotrc.kps` only:

```bat
py -3 patch_staging\A006_FORCEGRID_WINDOWS_RECOVERY_v0.5.0c2\repair.py --base . --rollback
```

No runtime checkpoints, original geometry, or generated ForceGrid output is removed by rollback.
