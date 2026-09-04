# SP02 — Compatibility junction layer, stage 1

Status: `PLANNED` · Priority: P0 · Risk: low · Depends on: SP01, SP03

This is what makes the migration non-breaking. After a family moves, a junction at its old root
keeps all ~2,064 hardcoded references working, unchanged, until SP11 removes them.

## Why junctions and not symlinks

`mklink /J` creates a directory junction, which on Windows requires **no administrator rights and
no developer mode**. `mklink /D` creates a symbolic link, which requires one or the other. Since
every developer and every scheduled campaign run must be able to recreate this layer after a fresh
clone, junctions are the only option that works unattended.

Junctions also resolve at the filesystem level, so `.cmd` scripts, Python, C++ and the KnotPlot
executable all traverse them without knowing.

Limitation to accept: junctions are local-only and cannot point across volumes. Everything here is
on one volume, so this does not bite.

## The critical detail: git must not see through the junction

If `KnotPlot/` moves to `03_data/A_knots/A001_knotplot_relaxed/` and a junction is created at
`KnotPlot/`, git will walk into the junction and see 8,285 tracked files at a path it thinks is
newly untracked. `git add -A` would then double-track the entire tree.

Junction names therefore go in **`.git/info/exclude`**, not `.gitignore`:

- `.git/info/exclude` is machine-local and uncommitted, which is correct — junctions are a local
  compatibility artifact, not repository content.
- `.gitignore` is committed and would follow the repo to machines where the junctions do not exist,
  and worse, would silently ignore a *real* directory if someone recreated one by hand.

This distinction is the single most likely thing to go wrong in the whole migration. Verify it on
the first junction before creating the other 72.

## Deliverables

### 1. `07_scripts/junctions.py`

```text
junctions.py create   [--phase SP04] [--dry-run]
junctions.py verify
junctions.py remove   [--phase SP04] [--dry-run]
junctions.py status
```

Reads `path_map.csv`, acts on rows with `junction=yes` and `status=moved`. Writes
`10_docs/migration/junction_registry.csv` recording `old_path,target,created_at,phase`.

`create` also appends the junction name to `.git/info/exclude` if absent. `remove` strips it again.

### 2. `07_scripts/bootstrap_junctions.cmd`

One command that rebuilds the entire compat layer after a fresh clone. Without this, a clone is
broken for every pack that has not yet been converted to the resolver.

### 3. Recreate-on-clone documentation

`10_docs/migration/junctions.md`: what they are, why they exist, when they disappear, and the
single command to restore them.

## Verification, and why `Test-Path` is not enough

A junction that exists but points at the wrong target passes a naive existence check. The guard
test must compare identity, not presence:

```powershell
(Get-Item KnotPlot).LinkType          # -> Junction
(Get-Item KnotPlot).Target            # -> the expected absolute target
```

and then confirm a known file is reachable through both paths and is the same file — compare size
and SHA-256 against `checksums.sha256` from SP00, not just `Test-Path`.

## Tests to write

- `test_junctions.py` — `create` is idempotent; `verify` fails on a junction pointing at the wrong
  target; `verify` fails on a real directory sitting where a junction should be; `remove` is safe
  when the junction is already gone; `.git/info/exclude` is updated exactly once per name.
- `test_junction_git_invisibility.py` — after creating a junction over a moved tree,
  `git status --porcelain` reports no new untracked files. This is the regression test for the
  failure mode described above.
- `test_bootstrap.py` — on a scratch copy, `bootstrap_junctions.cmd` reconstructs every registry
  row and `verify` passes.

## Rollback

`junctions.py remove --phase <SP>` deletes the junctions and cleans `.git/info/exclude`. Junction
removal never touches the target, so rollback is free. If a junction is deleted with
`Remove-Item -Recurse` instead of `rmdir /S` on the junction itself, Windows can follow it into the
target — `junctions.py remove` must use the safe call and its test must prove the target survives.

## Done criteria

- Every row with `junction=yes` and `status=moved` has a live, correctly-targeted junction.
- `git status --porcelain` is clean after junction creation.
- `bootstrap_junctions.cmd` reconstructs the layer from scratch on a fresh clone.
- All three test files pass.
- At least one pack that has *not* been converted to the resolver runs successfully through its old
  hardcoded path. That is the actual proof this layer works.
