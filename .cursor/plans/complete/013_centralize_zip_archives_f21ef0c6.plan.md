---
name: Centralize zip archives
overview: Move all Workbench `.zip` archives into a single nested tree under `Restore_Archives/<theme>/…`, reorganize the existing flat Downloads dump, and update the inventory docs. Research packs keep only their extracted working trees.
todos:
  - id: script
    content: Add scripts/consolidate_archives.py with theme rules, dry-run/apply, collision handling, _MANIFEST.csv + unit tests
    status: completed
  - id: reorganize-restore
    content: "Apply: move Restore_Archives/Sources_Zips/*.zip into theme folders; remove empty Sources_Zips"
    status: completed
  - id: move-repo-zips
    content: "Apply: move all remaining Workbench *.zip into Restore_Archives/<theme>/ with collision rule"
    status: completed
  - id: docs
    content: Write Restore_Archives/README.md; update INVENTORY_ARCHIVES.md and INVENTORY.md
    status: completed
  - id: verify
    content: Re-scan for stray zips; run consolidate + scripts + gilbert tests
    status: completed
isProject: false
---

# Centralize zip archives under Restore_Archives

## Decisions (locked)

- **1A — Move**, not copy: after consolidation, research packs hold only extracted trees; zips live only under [`Restore_Archives/`](c:\workspace\projects\SST-Workbench\Restore_Archives).
- **2A — Theme nesting**: `Restore_Archives/<theme>/<optional_series>/`.

## Target layout

```
Restore_Archives/
  README.md                 # how to find a pack; points at INVENTORY_ARCHIVES.md
  _MANIFEST.csv             # every zip: theme, series, basename, size, sha256, source_path
  Python/                   # keep existing 112 loose .py files (unchanged location for now)
  Fermat/
  RouteB_BEM/
  ChiPhase/                 # optional subdirs TrackB_v10B1_v16B0/, chiE/
  Coil/
  VortexLab/
  DeriveConstants/
  Falsifiers/               # minimal harness, Sutcliffe, dark-knot, …
  Dimensionless/
  ContactBilliard/
  Route_I/
  Routes_v0819/
  Trefoil/
  Hopf/
  Horn_SSDL/
  FS_Attachment/
  Bridge/                   # contra-swirl, timefield, CASTLE/Eckvahl
  KnotPlot/                 # KnotPlot, ridgerunner, fseries data zips
  SST21D/
  ProofScripts/
  Datasets/
  TripleGear/
  Templates/
  Canon/                    # SST_CANON / NotebookLM / architecture patches (split out of Misc)
  Misc/                     # leftover after rules + one manual pass
```

Series subfolders only where useful (e.g. `Fermat/v0.6.1/`, `VortexLab/v7.6-release-train/`). Otherwise flat under the theme.

## Collision rule (basename already in Restore_Archives)

When moving a repo zip whose basename already exists under `Restore_Archives/`:

1. Compare **size + SHA256**.
2. If identical → delete the repo copy (Downloads/central already has it).
3. If different → keep both: move repo zip as `<stem>__from_repo.zip` next to the existing file (no silent overwrite).

## Execution steps

### 1. Inventory + dry-run script

Add [`scripts/consolidate_archives.py`](c:\workspace\projects\SST-Workbench\scripts\consolidate_archives.py) (+ [`scripts/test_consolidate_archives.py`](c:\workspace\projects\SST-Workbench\scripts\test_consolidate_archives.py)):

- Classify basename → theme/series via ordered regex rules (same heuristics as above + Canon / ContactBilliard / Datasets / Templates / ProofScripts fixes for current Misc bleed).
- Modes: `--dry-run` (default) then `--apply`.
- Emits `_MANIFEST.csv` and a move log.
- Skips `.git`, `.venv`, `node_modules`, and anything already under `Restore_Archives/` when scanning sources.
- Does **not** move non-zip files (except leaving `Python/` alone).

### 2. Reorganize existing `Sources_Zips/`

- Move the 289 flat zips from [`Restore_Archives/Sources_Zips/`](c:\workspace\projects\SST-Workbench\Restore_Archives\Sources_Zips) into theme folders.
- Remove empty `Sources_Zips/` when done.

### 3. Move repo zips (~146)

- Scan whole Workbench for `*.zip` outside `Restore_Archives/`.
- Move into matching theme (collision rule above).
- Notable sources: `KnotPlot/`, `SST_fermat_pybind_research/`, `SST_Route_I_…/`, `GUI/vortexring-lab/…-release-train/`, `bundles/`, `SST_routeB_…/`, `proof-scripts/`, nested campaign/results zips inside version folders.

### 4. Docs

- Write [`Restore_Archives/README.md`](c:\workspace\projects\SST-Workbench\Restore_Archives\README.md): layout, collision rule, “working trees stay in research packs”.
- Update [`INVENTORY_ARCHIVES.md`](c:\workspace\projects\SST-Workbench\INVENTORY_ARCHIVES.md): central home is now `Restore_Archives/`; paired state = theme zip + extracted pack elsewhere; refresh counts after move.
- Short note in [`INVENTORY.md`](c:\workspace\projects\SST-Workbench\INVENTORY.md) under layout / flags.
- Do **not** edit the inventory plan file itself.

### 5. Verify

- Dry-run then apply; assert zero `*.zip` remain outside `Restore_Archives/` (except if any path is gitignored and recreated — re-scan once).
- `python -m pytest scripts/test_consolidate_archives.py` + existing `scripts/` tests + `unittest test_sst_gilbert_usability`.
- Spot-check: Fermat v0.6.1 zip under `Restore_Archives/Fermat/`, extracted tree still at `SST_fermat_pybind_research/…_v0.6.1/`.

## Out of scope

- Unpacking zip-only lineages (Route-I v0.1.0, etc.).
- Deduplicating extracted working trees or `Knots_FourierSeries` mirrors.
- Deleting `.tmp.driveupload` or nested `.venv`.
- Moving the 112 loose `Restore_Archives/Python/*.py` files (stay put; optional later pass).
