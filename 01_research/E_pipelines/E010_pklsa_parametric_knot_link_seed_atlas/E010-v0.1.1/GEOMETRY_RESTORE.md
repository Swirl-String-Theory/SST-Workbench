# Geometry restore status — 2026-09-21

## Attempted sources

| Source | Result |
|--------|--------|
| `rclone gdrive:SST-Workbench` (earlier) | Path was in trash / not found |
| `rclone gdrive:SST-Workbench` + [Drive folder](https://drive.google.com/drive/folders/1pzxYzUMFbrl8A10TtEE8mbhCExm2JiU1) (recheck 2026-09-21 ~22:00) | **Root restored and listable** |
| Drive `…/E010_pklsa_…/` | Only **E010-v0.3.0** + zip/sha256; no v0.1.1 npz tree |
| Drive `A041-v0.4.1/datasets/SST_Parametric_Knot_Link_Seed_Atlas_v0.1.1/` | Same metadata as local; **`families/` and `base_geometries/` directory not found** |
| Drive `03_data/_rclone_bundles/` | KnotPlot/campaign/generated zips; **no PKLSA atlas zip** |
| Local `09_archive/` | No `SST_Parametric_Knot_Link_Seed_Atlas_v0.1.1` zip |
| Downloads `E010_pklsa_*_v0.3.0.zip` | Workbench-native E010 pipeline; **no** v0.1.1 `*.npz` bundles |
| `SST_Parametric_Trefoil_Seed_Atlas_v1.0.0.zip` | Hash matches `SOURCE_HASHES.json` (`11b7eb4e…`); trefoil-only upstream |
| `Ideal_Sources_Official.zip` | **Not found** locally (required for Gilbert Fourier rebuild) |

## Missing payload

`PACKAGE_MANIFEST.json` lists **98** `*.npz` files under `families/` and `base_geometries/`. None are present on local disk **or** on the restored Drive tree. Root `.gitignore` ignores `*.npz`, so they were never git-tracked.

## Policy

Do **not** invent geometries. `verify_atlas.py` cannot PASS until the signed npz set is restored from an authentic archive.

Canonical latest family version is **E010-v0.3.0** (source-resolution / qualification pipeline). This **v0.1.1** tree is retained as provenance for the seed-atlas packaging format and A041 adapter contract.

## A041 mirror

Not mirrored: nothing authentic to copy into `A041-v0.4.1/datasets/.../families|base_geometries`.
