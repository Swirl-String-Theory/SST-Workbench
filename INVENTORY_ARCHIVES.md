# SST-Workbench — archive inventory (bundles)

Companion to [INVENTORY.md](INVENTORY.md). Updated **2026-08-24** after Downloads
ingest, Workbench stray cleanup, and root-zip theme sort.

## Central home: `Restore_Archives/`

**Samenvatting:** 563 zip-pakketten (~2,4 GB) met SST-onderzoekssnapshots (Fermat, BEM,
chi-phase, coil, falsifiers, Maxwell, Route-I, routes, trefoil, ideal-links, …),
VortexRing Lab, KnotPlot-data en CANON-patches; working trees blijven in de research
packs, ~80 zips nog in `Misc/`.

All Workbench `.zip` files now live under theme folders in
[`Restore_Archives/`](Restore_Archives/). Research packs keep **extracted working
trees only**. Per-thema 1–3 zinnen: [`Restore_Archives/README.md`](Restore_Archives/README.md)
§ *Per thema*.

Consolidation tool: [`scripts/consolidate_archives.py`](scripts/consolidate_archives.py)
(manifest: `Restore_Archives/_MANIFEST.csv`). Phases: Sources_Zips → repo strays →
`Restore_Archives/` root → Misc reclassify.

`.gitignore` excludes `*.zip` — local-only, not in git.

| Measure (2026-08-24) | Value |
|----------------------|------:|
| Zips under `Restore_Archives/` | **563** |
| Total size | **~2406 MB** |
| Last consolidate ops | 67 Sources + 142 repo + 19 root (228 manifest rows) |
| Stray zips outside `Restore_Archives/` | **0** (excl. `.venv`) |
| Zips in `Restore_Archives/` root | **0** |

A **bundle** = theme zip under `Restore_Archives/<theme>/` plus the version-notated
extracted folder elsewhere (e.g. `SST_fermat_pybind_research/…_v0.6.1/`).

### Theme counts

| Theme | Zips |
|-------|-----:|
| Falsifiers | 93 |
| Misc | 80 |
| VortexLab | 43 |
| KnotPlot | 42 |
| ChiPhase | 34 |
| DeriveConstants | 29 |
| RouteB_BEM | 27 |
| Fermat | 26 |
| Trefoil | 20 |
| Coil | 22 |
| IdealLinks | 21 |
| Canon | 19 |
| Maxwell | 15 |
| Route_I | 12 |
| Routes_v0819 | 11 |
| FS_Attachment | 10 |
| Dimensionless | 10 |
| Datasets | 8 |
| Hopf | 7 |
| KelvinFloquet | 6 |
| Bridge | 6 |
| TripleGear | 6 |
| SST21D | 4 |
| Templates | 4 |
| Horn_SSDL | 3 |
| ProofScripts | 3 |
| ContactBilliard | 2 |

Content-differing basename collisions kept as:
`sst_chi_phase_package__from_repo.zip`,
`sst_chi_phase_package_v6__from_repo.zip`,
`SST_cpp_pybind_audit_template__from_repo.zip`.

---

## Code that exists only inside archives

These **13 scripts** are nowhere in the working tree (only inside zips). Paths are
now under `Restore_Archives/`:

### `Restore_Archives/Route_I/` (worst case)

Nine Route-I archives; **only `v0.0.4` was extracted** into
`SST_Route_I_relative_entropy_PoC/`. Eight scripts live only in zips:

| Archive (under `Restore_Archives/Route_I/`) | Script only in zip |
|---------------------------------------------|--------------------|
| `SST_Route_I_relative_entropy_PoC.zip` | `sst_relative_entropy_route1_poc.py` |
| `…_v0.0.2.zip` | `sst_relative_entropy_route1_poc_v0.0.2.py` |
| `…_v0.0.5.zip` | `sst_route1_parallel_hierarchy_v0.0.5.py` |
| `…_v0.0.6.zip` | `sst_route1_common_foundation_v0.0.6.py` |
| `…_v0.0.7.zip` | `sst_route1_nonlinear_adjacency_phase_v0.0.7.py` |
| `…_v0.0.8.zip` | `sst_route1_beta_selection_v0.0.8.py`, `legacy_v0_0_7.py` |
| **`…_v0.1.0.zip`** (newest) | **`sst_route1_resolved_knot_action_v0.1.0.py`** |

`v0.1.0` targets resolved-knot action (I_K, Ω_K, β_Q), not the extracted v0.0.4
relative-entropy PoC. See [INVENTORY_PYTHON.md](INVENTORY_PYTHON.md) § Route-I.

### Other unique-in-zip scripts

| Theme location | Script(s) only in zip |
|----------------|------------------------|
| `Restore_Archives/Routes_v0819/` (`…_A_to_D_evidence_pack.zip`) | `apply_planck_routes_patch_v0_8_19.py`, `sst_planck_routes_A_to_D_candidate_summary.py` |
| `Restore_Archives/TripleGear/triple_gear_parametric_recovery_phase1.zip` | `triple_gear_parametric_recovery.py` |
| `Restore_Archives/ProofScripts/SST_Fseries.zip` / `VAM_Fseries.zip` | `vamcore_batch_hypvol_from_fseries.py` |

### Orphan zips whose Python is fully mirrored on disk

Nothing hidden despite never being unpacked as a sibling folder of the zip’s old path
(content already exists as extracted trees):

| Archive theme | Note |
|---------------|------|
| `Trefoil/` (`trefoil_closure.zip`, etc.) | Content under `SST_Trefoil_Closure/` |
| `Hopf/` | Mirrored by `SST_Hopf_Benchmark_Packet_v0.1/` |
| `Falsifiers/` (Sutcliffe) | Extracted under `SST_Sutcliffe_HSS_feasibility_gate/` |
| `Routes_v0819/` trial / heat-guard bundles | Also under live packs / legacy_scripts |

---

## How to re-consolidate

```powershell
python scripts/consolidate_archives.py          # dry-run
python scripts/consolidate_archives.py --apply  # move
```

Collision rule: identical size+SHA256 → delete duplicate; different content →
`<stem>__from_repo.zip`.

---

## Historical note (pre-2026-08-05)

Before centralization there were ~140 zips scattered beside research packs (~640 MB),
plus a flat Downloads dump in `Restore_Archives/Sources_Zips/` (~289 zips). Those
are now merged into the theme tree above. Older “paired / zip-only / folder-only”
path listings referred to those scattered locations.
