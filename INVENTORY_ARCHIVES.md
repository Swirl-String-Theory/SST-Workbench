# SST-Workbench — archive inventory (bundles)

Companion to [INVENTORY.md](INVENTORY.md). Updated **2026-08-05** after zip
centralization.

## Central home: `Restore_Archives/`

**Samenvatting:** 368 zip-pakketten (~1,3 GB) met SST-onderzoekssnapshots (Fermat, BEM,
chi-phase, coil, falsifiers, Route-I, routes, trefoil, …), VortexRing Lab, KnotPlot-data
en CANON-patches; working trees blijven in de research packs, ~60 zips nog in `Misc/`.

All Workbench `.zip` files now live under theme folders in
[`Restore_Archives/`](Restore_Archives/). Research packs keep **extracted working
trees only**. Per-thema 1–3 zinnen: [`Restore_Archives/README.md`](Restore_Archives/README.md)
§ *Per thema*.

Consolidation tool: [`scripts/consolidate_archives.py`](scripts/consolidate_archives.py)
(manifest: `Restore_Archives/_MANIFEST.csv`).

`.gitignore` excludes `*.zip` — local-only, not in git.

| Measure (2026-08-05) | Value |
|----------------------|------:|
| Zips under `Restore_Archives/` | **368** |
| Total size | **~1259 MB** |
| Last consolidate ops | 289 theme moves from Downloads dump + 88 repo moves + 56 duplicate deletes + 2 renames |
| Stray zips outside `Restore_Archives/` | **0** |

A **bundle** = theme zip under `Restore_Archives/<theme>/` plus the version-notated
extracted folder elsewhere (e.g. `SST_fermat_pybind_research/…_v0.6.1/`).

### Theme counts

| Theme | Zips |
|-------|-----:|
| VortexLab | 43 |
| ChiPhase | 34 |
| RouteB_BEM | 27 |
| Fermat | 26 |
| Coil | 22 |
| DeriveConstants | 20 |
| Canon | 19 |
| KnotPlot | 17 |
| Trefoil | 14 |
| Route_I | 12 |
| Routes_v0819 | 11 |
| Falsifiers | 10 |
| FS_Attachment | 10 |
| Dimensionless | 9 |
| Datasets | 8 |
| Bridge | 6 |
| TripleGear | 6 |
| ProofScripts | 3 |
| Horn_SSDL | 3 |
| SST21D | 3 |
| ContactBilliard | 2 |
| Hopf | 2 |
| Templates | 1 |
| Misc | 60 |

Content-differing basename collisions kept as:
`sst_chi_phase_package__from_repo.zip`,
`sst_chi_phase_package_v6__from_repo.zip`.

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
