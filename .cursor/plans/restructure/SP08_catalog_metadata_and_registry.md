# SP08 — Catalog metadata and registry

Status: `PLANNED` · Priority: P3 · Risk: medium · Depends on: SP06, SP07

Every family now sits at its catalog path. This sub-plan makes the catalog *machine-readable* and
turns the version identifiers into something a program can compare.

Until this runs, `falsifier_registry.yaml` is broken: all 46 entries resolve packs by `pack_glob`
against top-level directory names that no longer exist.

## 1. `FAMILY.yaml`

One per family, completing the stubs written in SP05 and SP06.

```yaml
catalog_id: A039
domain: 01_research
letter: A_falsifiers
name: SST Quantum Galileo Action Gauge Closure Falsifier
kind: falsifier            # falsifier | closure | dynamics | benchmark | pipeline | exploratory
                           # library | dataset | tool | app
status: active             # active | dormant | superseded | archived
latest: v0.1.1
versions:
  - id: v0.1.0
  - id: v0.1.1
    blind: true
    key: keys/v0.1.1_REVEAL_KEY
variants: []
legacy_paths:
  - SST_Quantum_Galileo_Action_Gauge_Closure/
output_prefix: SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier
```

`output_prefix` is what preserves the output convention. A run from
`A039_.../A039-v0.1.1/` produces `SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.1-outputs/`
because the prefix comes from here, not from the directory name. Without this field, SP09's rename
would silently change every output artifact name.

`legacy_paths` is what makes the migration auditable forever: given any pre-migration path from a
paper, a zip or a lab notebook, the family that owns it is findable.

## 2. `project.json`

One per version directory, so a version copied loose stays identifiable — the reason for the
`A039-v0.1.1` naming in the first place.

```json
{
  "catalog_id": "A039",
  "name": "SST Quantum Galileo Action Gauge Closure Falsifier",
  "version": "v0.1.1",
  "revision": null,
  "legacy_dir": "SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.1"
}
```

`legacy_dir` records the pre-SP09 directory name. After SP09 renames directories, this is the only
place the original name survives at version level.

## 3. Version normalization rules

The rule, stated once:

```text
project identity  !=  version identity  !=  experiment variant
```

Applied three ways. **No directory is renamed here** — SP09 does that. This sub-plan only records
the intended normalization in `project.json` and `FAMILY.yaml`.

**Four-part identifiers** become three-part plus a revision:

| Current | Version | Revision |
|---------|---------|---------:|
| `v0.2.2.5` (A032) | `v0.2.2` | 5 |
| `v0.2.2.8` (A032) | `v0.2.2` | 8 |
| `v0.1.2.2` … `v0.1.2.4` (`02_libraries/C001`) | `v0.1.2` | 2 … 4 |
| `v0.2.1.1`, `v0.3.5.1`, `v0.3.6.1` (D003) | `v0.2.1`, `v0.3.5`, `v0.3.6` | 1 |
| `v0.1.2.1`, `v0.1.3.1` (A005) | `v0.1.2`, `v0.1.3` | 1 |

Directory form after SP09: `A032-v0.2.2-r8`.

**Configuration baked into the version** moves to a config file:

| Current | Version | Config |
|---------|---------|--------|
| `v0.4.6_DD32_compact` (A021) | `v0.4.6` | `configs/dd32-compact.json` |
| `v0.4.7_HR_DD32_Ladder_compact` (A021) | `v0.4.7` | `configs/hr-dd32-ladder-compact.json` |
| `v0.4.8_Adaptive_Spectral_DD32_compact` (A021) | `v0.4.8` | `configs/adaptive-spectral-dd32-compact.json` |
| `v0.2.0_infinite_background_vortex` (A002) | `v0.2.0` | `configs/infinite-background-vortex.json` |
| `v0.3.0_axial_vortex_bundle` (A002) | `v0.3.0` | `configs/axial-vortex-bundle.json` |
| `v0.4.0_iso_gamma_area_dynamic_clock` (A002) | `v0.4.0` | `configs/iso-gamma-area-dynamic-clock.json` |
| `v0.2.0_Gilbert` (A003) | `v0.2.0` | `configs/gilbert.json` |
| `v8_exact_rodin`, `v9_complete`, `v10_complete_restored` (F003) | `v8`, `v9`, `v10` | `configs/*.json` |
| `v0.4.3_flat` (C007) | `v0.4.3` | `configs/flat.json` |

Extracting the config file itself is **not** in scope. The recorded mapping is enough for SP09 to
rename correctly; producing real config files is per-family work done when a family is next touched.

**Closed historical series stay as they are.** C001's `v10B1`–`v16B0` and C002's `local0`, `_v4`–`_v7`
are documented exceptions in `FAMILY.yaml`, not renamed. Mapping a closed series onto semver
invents precision that was never there.

**Old identifiers are never rewritten in place.** Only new versions follow the new convention. Every
old identifier lives in `legacy_paths`, `legacy_dir` and `path_map.csv`.

## 4. `falsifier_registry.yaml` migration

The registry's 46 entries resolve through `pack_glob`, matched against directory and zip names.
Every glob is now stale.

- Add `catalog_id` to each entry.
- Change `scripts/falsifier_registry.py` resolution from glob matching to catalog lookup via
  `sst_workbench_paths.resolve_family()`.
- Keep `pack_glob` as a **deprecated** field used only for resolving names inside
  `09_archive/restore/`, where zip filenames still carry the old naming and always will.
- `--discover` must now find families without a `catalog_id` and families in `CATALOG_v0.1.md`
  without a registry entry. Both are real gaps worth reporting.

The 46 registry entries cover fewer families than the 40 falsifiers in the catalog plus the
closures and dynamics families. Reconciling the two lists is part of this step, and the mismatch is
itself a finding to record.

## 5. Catalog index

Generate `10_docs/registry/catalog_index.json` from every `FAMILY.yaml`, so `resolve_family()` does
one file read rather than a tree walk. Rebuilt by `07_scripts/build_catalog_index.py`, verified in
CI-style by a test that the index matches the tree.

## 6. `INVENTORY.md` regeneration

`INVENTORY.md` still says `Snapshot date: 2026-08-04` while quoting 2026-09-03 statistics. Regenerate
it, and `INVENTORY_TREE.json`, against the catalog. `workbench_tree.py`'s notion of a family changes
from "top-level directory" to "directory containing `FAMILY.yaml`" — the guarded change made in
SP04 becomes the only path here.

## Tests to write

- `test_family_yaml.py` — every family directory has a `FAMILY.yaml`; every one parses; every
  `catalog_id` is unique and matches `CATALOG_v0.1.md`; `latest` names a version that exists;
  `output_prefix` is present and non-empty for every family that produces outputs.
- `test_project_json.py` — every version directory has a `project.json` whose `catalog_id` matches
  its parent family and whose `version` matches its directory name.
- `test_registry_catalog_sync.py` — every `falsifier_registry.yaml` entry has a resolvable
  `catalog_id`; every catalog family of kind `falsifier` has a registry entry, or an explicit
  documented exemption.
- `test_version_normalization.py` — every four-part identifier has a recorded `version` + `revision`
  split; every config-in-version name has a recorded config target; no normalization loses
  information.
- `test_catalog_index.py` — the generated index matches a fresh tree walk.

## Rollback

Metadata-only. Delete the `FAMILY.yaml` and `project.json` files and revert
`falsifier_registry.yaml` and `falsifier_registry.py`. No directory changes to undo.

## Done criteria

- Every one of the 109 catalog families has a complete `FAMILY.yaml`.
- Every version directory has a `project.json`.
- `falsifier_registry.py --validate` passes against catalog IDs; `--discover` reports zero
  unregistered falsifier families or an explicit exemption list.
- `INVENTORY.md` and `INVENTORY_TREE.json` regenerated with a correct snapshot date.
- All five test files pass.
