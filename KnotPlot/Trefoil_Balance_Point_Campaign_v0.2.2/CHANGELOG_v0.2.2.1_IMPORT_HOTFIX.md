# v0.2.2.1 import hotfix

Observed Windows failure:

```text
SOURCE: ...\Trefoil_Balance_Point_Campaign_v0.2.1
shutil.copy2(...)
FileNotFoundError: [WinError 3]
```

This occurs before any 60k->100k KnotPlot continuation.

Fix:
- scientific preregistration and `balance_design.json` are untouched;
- source auto-selection now prefers repaired packed `*_outputs*.zip` files;
- a sibling v0.2.1 folder is selected only when all required 0/30k/40k/50k/60k
  coordinates plus all 20 `i60000.k` states are present;
- `shutil.copy2` / Windows CopyFile2 is no longer used;
- file copies use byte streams into a temporary destination followed by replace;
- incomplete candidate sources are reported and skipped;
- `TREFOIL_V021_SOURCE` and `--source` remain supported.

After overlay, simply rerun:

```bat
run_all.cmd
```

The failed attempt had not begun the 60k->100k KnotPlot continuation.
