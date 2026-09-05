Catalog registry and FAMILY index (SP08).

| File | Role |
|------|------|
| `catalog_index.json` | Compact index for `sst_workbench_paths.resolve_family()` — regenerate with `python 07_scripts/build_catalog_index.py` |
| `family_hierarchy.json` | Full hierarchy with version dirs + output zip names + naming conventions for new packs — regenerate with `python 07_scripts/build_family_hierarchy.py` |

Never hand-edit the generated JSON; update `FAMILY.yaml` (and on-disk version folders), then rebuild.
