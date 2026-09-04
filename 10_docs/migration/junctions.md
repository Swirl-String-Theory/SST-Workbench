# Compatibility junctions (SP02)

Junctions keep pre-restructure hardcoded paths working after packs move.
They are a **local, recreate-on-clone** layer — not repository content.

## Policy

| Rule | Why |
|------|-----|
| Use `mklink /J` (directory junction) | No admin rights, no Developer Mode; works unattended after clone |
| Do **not** use `mklink /D` (symlink) | Requires elevation or Developer Mode |
| Put junction names in **`.git/info/exclude`**, never `.gitignore` | Exclude is machine-local; `.gitignore` would follow clones and could hide a real directory |
| Remove with `os.rmdir` / `rmdir` on the junction only | `Remove-Item -Recurse` can follow into the target and delete real files |
| Junctions stay on one volume | Windows junctions cannot cross volumes |

## Lifecycle

1. **SP04+** move a family with `git mv` (`status=moved` in `path_map.csv`).
2. `junctions.py create` places a junction at `old_path` → `new_path` and records it in
   `junction_registry.csv`.
3. Hardcoded references keep working until packs are converted to
   `sst_workbench_paths` / `07_scripts/paths.cmd`.
4. **SP11** removes junctions after conversion; targets are never deleted by `remove`.

## Recreate after clone

```bat
07_scripts\bootstrap_junctions.cmd
```

Or:

```bat
python 07_scripts\junctions.py create
python 07_scripts\junctions.py verify
```

Requires: rows in `path_map.csv` with `junction=yes` and `status=moved`, and the
destination directories present on disk.

## Commands

```text
python 07_scripts/junctions.py create   [--phase SP04] [--dry-run]
python 07_scripts/junctions.py verify   [--phase SP04]
python 07_scripts/junctions.py remove   [--phase SP04] [--dry-run]
python 07_scripts/junctions.py status   [--phase SP04]
```

## Verification (identity, not presence)

```powershell
(Get-Item KnotPlot).LinkType   # Junction
(Get-Item KnotPlot).Target     # expected absolute new_path
```

Then confirm a known file is reachable through both paths (same size / SHA-256).
`Test-Path` alone is not enough — a junction can exist and still point at the wrong target.

## First live junction

Before creating the remaining junctions, create **one** junction, confirm
`git status --porcelain` stays clean, then proceed. That check is automated in
`scripts/test_junction_git_invisibility.py`.
