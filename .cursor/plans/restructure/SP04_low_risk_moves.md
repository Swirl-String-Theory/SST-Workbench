# SP04 — Low-risk moves

Status: `PLANNED` · Priority: P1 · Risk: low · Depends on: SP02, SP03

Eighteen roots that need no semantic decision. This phase exists to prove the machinery — the
mover, the junctions, the manifest, the verification — on material where a mistake is cheap,
before SP05 touches research families.

## Order

Deliberate: least-referenced first, so the first junction ever created protects almost nothing.

| Order | Root | Destination | Why low risk |
|------:|------|-------------|--------------|
| 1 | `KnotTheory/` | `08_third_party/knot_theory/` | Vendored, ~15 external references, all documentation |
| 2 | `templates/` | `06_templates/` | ~15 references, self-contained audit templates |
| 3 | `bundles/` | `09_archive/bundles/` | One zip, zero code references |
| 4 | `generated-figures/` | `03_data/D_generated/D002_figures/` | ~2 references |
| 5 | `SST-dashboard/` | `05_apps/A001_dashboard/` | Standalone PyQt5 app, no inbound references |
| 6 | `proof-scripts/` | `04_tools/D_proof/D001_proof_scripts/` | ~2 references |
| 7 | `Restore_Archives/` | `09_archive/restore/` | 607 zips, 115 tracked, zero code references |
| 8 | `Fremlin_FourierSeries/` | `03_data/A_knots/A006_fremlin_fourier_series/` | ~14 references |
| 9 | `Ideal_Sources/` | `03_data/A_knots/A004_ideal_gilbert/` | ~95 references — first real junction test |
| 10 | `Katlas_Sources_v0.2.2_Outputs/` | `03_data/A_knots/A005_katlas_sources/v0.2.2/` | ~86 references |
| 11 | `Katlas_Source_Crawler_v0.2.2/` | `04_tools/B_crawlers/B001_katlas_source_crawler/v0.2.2/` | Self-contained |
| 12 | `PTSA_Parametric_Trefoil_Seed_Atlas_v1.0.0/` | `03_data/A_knots/A008_parametric_trefoil_seed_atlas/v1.0.0/` | New, few references |
| 13 | `datasets/` | `03_data/B_external/B001_sparc_and_papers/` | ~136 references, mostly output seals |
| 14 | `media/` | `03_data/C_reference/C001_media/` | Assets only |
| 15 | `scripts/` | `07_scripts/` | Test command changes — see below |
| 16 | Root docs | `10_docs/inventory/`, `10_docs/migration/` | Documentation |
| 17 | Root loose scripts | `07_scripts/` | `sst_gilbert_usability.py` + test, `rhof_eligibility_scan.py` |
| 18 | Root zips and data files | `09_archive/restore/`, `03_data/A_knots/A004_ideal_gilbert/` | `knots_ideal_favorites.txt`, `rhof_triage.csv`, three root zips |

## Per-move procedure

Identical for all eighteen. If any step fails, stop and revert that move — do not continue to the
next.

1. Write or update the `path_map.csv` row, `status=pending`.
2. `git mv <old> <new>` (or `robocopy /MOVE` for untracked residue, if SP00 Q1 showed it is needed).
3. `junctions.py create --phase SP04` for this row.
4. `git status --porcelain` — must show only the rename, no new untracked files. If the junction is
   visible to git, the `.git/info/exclude` entry is missing; fix before continuing.
5. Verify a known file resolves identically through both old and new path, by SHA-256 against
   `checksums.sha256`.
6. Set `status=moved`, then `status=verified` after step 7.
7. Run the phase test suite.
8. Commit. **One commit per move**, message naming the catalog ID and both paths.

## The `scripts/` move needs care

Three things change with it:

- The documented test command becomes `python -m pytest 07_scripts/`. Update `README.md` and
  `10_docs/`.
- `scripts/test_workbench_tree.py` asserts on the literal names `KnotPlot` and `Knot_Library`;
  `scripts/test_consolidate_archives.py` asserts on `Knot_Library` for archive classification.
  These are **expected** to fail once SP04 moves `Restore_Archives/` and again when SP07 moves
  `KnotPlot/`. Update the assertions to read from `path_map.csv` rather than hardcoding names, so
  they stop being restructure-fragile.
- `scripts/workbench_tree.py` generates `INVENTORY_TREE.json` from the root. After the restructure
  it must walk the catalog, so its notion of "family" changes from "top-level directory" to
  "directory containing `FAMILY.yaml`". Do that change here, guarded so it works before and after.

Move `scripts/` **last** among the eighteen, so the tooling that verifies the other seventeen is
not itself in motion while they move.

## Tests to write

- `test_move_phase.py` — reusable harness: given a `path_map.csv` phase, assert every row is
  `verified`, every `new_path` exists, every `junction=yes` row has a correct junction, and no
  `old_path` contains real files any more.
- Update `test_workbench_tree.py` and `test_consolidate_archives.py` to resolve names through
  `path_map.csv`.

## Rollback

Per move, in reverse: `junctions.py remove` for that row, `git mv <new> <old>`, set
`status=reverted`. Because each move is its own commit, `git revert <sha>` plus a junction removal
is equally valid and preserves history.

## Done criteria

- All eighteen rows `status=verified`.
- `git status` clean; the working tree has no stray untracked directories.
- Baseline test suite matches SP00's recorded result, with the two expected assertion updates
  accounted for.
- At least three packs that reference moved data by their old hardcoded path run successfully
  without modification. `Ideal_Sources` (~95 references) is the one that matters.
