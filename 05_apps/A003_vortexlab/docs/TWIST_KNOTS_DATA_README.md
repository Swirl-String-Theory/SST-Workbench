# A006 twist catalog converter for VortexLab

This package contains:

- `twist_knot_data.js` — Fourier catalog generated from A006 RoundFolded Twist Knot Family XYZ centerlines. Pretty-printed like `knotplot_knots_data.js` (indent=2).
- `build_twist_knot_data.py` — converter/updater for those `.xyz` exports.

Also deployed to the modular app:

```text
05_apps/A003_vortexlab/apps/web/data/twist_knot_data.js
```

loaded from `apps/web/index.html` as `./data/twist_knot_data.js`.

## Current catalog (shipping thin set)

The checked-in catalog keeps the full multi-N / chirality **knot** set, short Seeds, one qualification export, and corrected A006 `SEEDS` **ROUND** geometry that **replaces** legacy geometry for topologies `4_1`, `7_2`, `8_1`, `9_2`, `10_1`, `11a247`. Torus knots `3_1` / `5_1` / `7_1` / `9_1` / `11a367` carry `family: torus-knot` and `selectorLabel`. TIKZ_NATIVE SEEDS variants are **not** included.

**Classic links are thinned for file size (&lt;50 MB):** only profiles `FLAT` and `SOFT`, only `N=512` and `N=1024`. `BALANCED` / `TIGHT` and link N256 / N2048 are omitted from the shipping JS.

| Source | Count | ID pattern |
|--------|------:|------------|
| Knots (`Output/v050/geometry` minus replaced topologies) | 44 | `KNOT_*_N####_{ORIG\|MIRROR}` |
| Classic links (FLAT/SOFT × N512/1024 only) | 32 | `LINK_*_{FLAT\|SOFT}_N{0512\|1024}_{chir}_{CP}` |
| `Output/Seeds` | 26 | `<topology>_N####` (kind=KNOT, chirality=ORIG) |
| `SEEDS` ROUND only | 36 | `KNOT_*_N####_{ORIG\|MIRROR}_ROUND` |
| `qualification_v050c/.../i0000128.xyz` | 1 | `QUAL_AMECH_140_ELEC_i0000128` |

**Total: 139 entries** (235 full catalog − 96 dropped classic LINK variants). Typical pretty-print size ≈ 33 MB.

UI defaults (Knot / FLAT / ORIG / N1024 / CPFIXED61) show a short filtered list. Set every filter to **All** to browse the shipping catalog.

Canonical copies:

```text
05_apps/A003_vortexlab/vortexring-lab/twist_knot_data.js
05_apps/A003_vortexlab/apps/web/data/twist_knot_data.js
```

## Source geometry

```text
02_libraries/A_knot_libraries/A006_RoundFolded_Twist_Knot_Family/A006-v0.5.0/Output/v050/geometry
02_libraries/A_knot_libraries/A006_RoundFolded_Twist_Knot_Family/A006-v0.5.0/Output/Seeds
02_libraries/A_knot_libraries/A006_RoundFolded_Twist_Knot_Family/A006-v0.5.0/SEEDS
02_libraries/A_knot_libraries/A006_RoundFolded_Twist_Knot_Family/A006-v0.5.0/Output/qualification_v050c/runs/AMECH_140_ELEC/i0000128.xyz
```

Filename patterns:

| Kind | Example |
|------|---------|
| Knot | `KNOT_3_1_N1024_ORIG.xyz` |
| Knot (11a) | `KNOT_11a367_N0512_MIRROR.xyz` |
| Knot SEEDS | `KNOT_4_1_N1024_ORIG_ROUND.xyz` (TIKZ_NATIVE omitted from catalog) |
| Link | `LINK_5_5_6_FLAT_N1024_ORIG_CPFIXED61.xyz` |
| Seed | `3_1_N1024.xyz` |
| Qualification | `i0000128.xyz` (via `--id` + metadata overrides; `Component N:` headers) |

Native A006 coordinates are preserved (not VortexLab uniform-N300 / D=1).

Qualification entries have `profile`/`cpMode` = null and appear under Link only when those filters are **All**.

## Generate / refresh (shipping thin catalog)

From `05_apps/A003_vortexlab/tools/catalog`:

```powershell
python .\build_twist_knot_data.py `
  --fresh `
  --apply-link-catalog-filter `
  --link-profiles FLAT,SOFT `
  --link-resolutions 512,1024 `
  --output ..\..\vortexring-lab\twist_knot_data.js `
  --scan "..\..\..\..\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0\Output\v050\geometry" `
  --scan "..\..\..\..\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0\Output\Seeds" `
  --glob "*.xyz"

python .\build_twist_knot_data.py `
  --output ..\..\vortexring-lab\twist_knot_data.js `
  "..\..\..\..\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0\Output\qualification_v050c\runs\AMECH_140_ELEC\i0000128.xyz" `
  --id QUAL_AMECH_140_ELEC_i0000128 `
  --kind LINK `
  --topology AMECH_140_ELEC `
  --chirality ORIG

python .\build_twist_knot_data.py `
  --force --relabel-torus --prune-replaced-knots `
  --output ..\..\vortexring-lab\twist_knot_data.js `
  --scan "..\..\..\..\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0\SEEDS" `
  --glob "*_ROUND.xyz"

python .\build_twist_knot_data.py `
  --prune-catalog `
  --link-profiles FLAT,SOFT `
  --link-resolutions 512,1024 `
  --output ..\..\vortexring-lab\twist_knot_data.js

Copy-Item ..\..\vortexring-lab\twist_knot_data.js ..\..\apps\web\data\twist_knot_data.js -Force
```

Expect **139** entries and file size under 50 MB. Pretty-print is the default; optional minify: `--compact`.

To prune an existing full catalog in place:

```powershell
python .\build_twist_knot_data.py --prune-catalog --output ..\..\apps\web\data\twist_knot_data.js
```

Legacy N1024 ORIG-only subset (29 files): use `--glob "*_N1024_*ORIG*.xyz"` on geometry alone (omit Seeds/qual/SEEDS).

## Entry schema (KnotPlot-like)

- `sourceRole`: `a006-native-N{N}`, `a006-seed-N{N}`, or `a006-qualification-N{N}`
- `source` / `sourceFormat` / `generator` / `ideal:false`
- `normalization.label|method|note` (`D` remains `null`)
- filter fields: `kind`, `topology`, `profile`, `resolutionN`, `chirality`, `cpMode`
- `family`: `classic-knot`, `torus-knot`, `classic-link`, `a006-seed`, or `a006-qualification`
- torus extras: `selectorLabel`, optional `torus` metadata

## UI defaults

| Filter | Default |
|--------|---------|
| kind | Knot |
| profile | FLAT (links only; BALANCED/TIGHT omitted from shipping catalog) |
| chirality | Original |
| N | 1024 |
| CP | CPFIXED61 (links only) |

Defaults keep the knot list short; All on every filter shows all 139 shipping IDs.

## Scientific status

Entries are A006 static/candidate geometries converted to discrete Fourier series for VortexLab sampling. They are **not** certified as global ideal/tight or ropelength-minimizing embeddings.

## Tests

```powershell
python -m unittest tests.test_build_twist_knot_data -v
```
