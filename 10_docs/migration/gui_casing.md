# SP03 — `gui` / `GUI` casing verification

**Result: no-op.** Index and filesystem already agree on lowercase `gui/`.

| Check | Result |
|-------|--------|
| `git ls-files 'gui/*'` count | 459 |
| `git ls-files` paths starting `GUI/` (case-sensitive) | 0 |
| Filesystem directory name | `gui` |

SP00 Q3 already recorded this. The temporary rename
(`git mv gui _gui_tmp` → `git mv _gui_tmp gui`) was **not** executed because it
would be a no-op commit. SP06 must continue to reference `gui/` (not `GUI/`)
when splitting into `05_apps/`.
