# KnotPlot catalog converter for VortexLab

This package contains:

- `knotplot_knots_data.js` — initial KnotPlot catalog containing `Tlink_6_9`, generated from `Tlink_6_9_D1_040k.txt`.
- `build_knotplot_knots_data.py` — converter/updater for future KnotPlot `.txt` exports.

## Initial generation

```powershell
python .\build_knotplot_knots_data.py `
  .\Tlink_6_9_D1_040k.txt `
  --output .\knotplot_knots_data.js
```

The canonical key is `Tlink_6_9`. A later checkpoint updates the same entry:

```powershell
python .\build_knotplot_knots_data.py `
  .\Tlink_6_9_D1_080k.txt `
  --output .\knotplot_knots_data.js
```

An older checkpoint is not allowed to overwrite a newer checkpoint unless `--force` is supplied.

## Scan a directory and update all matching D1 files

```powershell
python .\build_knotplot_knots_data.py `
  --scan . `
  --glob "*_D1_*k.txt" `
  --output .\knotplot_knots_data.js
```

## Keep every checkpoint as a separate catalog item

```powershell
python .\build_knotplot_knots_data.py `
  .\Tlink_6_9_D1_020k.txt `
  .\Tlink_6_9_D1_040k.txt `
  --keep-checkpoints `
  --output .\knotplot_knots_data.js
```

That produces IDs such as `Tlink_6_9_D1_020k` and `Tlink_6_9_D1_040k`.

## Merge A006 RoundFolded Seeds (`Output/Seeds`)

Canonical A006 seed stems such as `3_1_N1024` / `11a367_N2048` under
`A006-v0.5.0/Output/Seeds` are recognized by the converter. They are stored with
`family: "a006-twist"` and `sourceRole: "a006-seed-N…"` and listed **first** in
`KNOTPLOT_KNOT_IDS` so VortexLab can show an “A006 TWIST SEEDS” optgroup above
the classic KnotPlot groups.

Use `--strip-a006` to remove any previous A006 merge (e.g. wrong geometry-export
stems) before inserting Seeds:

From `05_apps/A003_vortexlab/tools/catalog`:

```powershell
python .\build_knotplot_knots_data.py `
  --strip-a006 `
  --scan "..\..\..\..\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0\Output\Seeds" `
  --glob "*.xyz" `
  --force `
  --output ..\..\apps\web\data\knotplot_knots_data.js
```

Current merged catalog size: **70** entries (26 A006 Seeds + 6 Borromean + 38 KnotPlot).

## Merge A006 Borromean links

Stage XYZ stems such as `Borromean_6_6_5_SOFT_MIN2048_S0800_v042d` and short
reference files `borromean_flat.txt` / `borromean_balanced.txt` become
`family: "a006-borromean"` and appear in the “A006 BORROMEAN” optgroup.

```powershell
python .\build_knotplot_knots_data.py --force --output ..\..\apps\web\data\knotplot_knots_data.js `
  "..\..\..\..\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0\Output\v050\_stage\6_6_5_SOFT_N2048_S0800\extensions\borromean\whole\references\borromean_flat.txt" `
  "..\..\..\..\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0\Output\v050\_stage\6_6_5_SOFT_N2048_S0800\extensions\borromean\whole\references\borromean_balanced.txt" `
  "..\..\..\..\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0\Output\v050\_stage\6_6_5_SOFT_N2048_S0800\output\borromean\Borromean_6_6_5_SOFT_MIN2048_S0800_v042d.xyz" `
  "..\..\..\..\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0\Output\v050\_stage\6_6_5_FLAT_N2048_S0800\output\borromean\Borromean_6_6_5_FLAT_MIN2048_S0800_v042d.xyz" `
  "..\..\..\..\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0\Output\v050\_stage\5_5_6_SOFT_N2048_S0800\output\borromean\Borromean_5_5_6_SOFT_MIN2048_S0800_v042d.xyz" `
  "..\..\..\..\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0\Output\v050\_stage\5_5_6_FLAT_N2048_S0800\output\borromean\Borromean_5_5_6_FLAT_MIN2048_S0800_v042d.xyz"
```

Pairwise Gauss linking ≈ 0 for these three-component candidates is expected for
Borromean rings (pairwise unlinked, collectively linked); it is not a converter error.

## Data model

Each component is converted to the same Fourier coefficient shape used by the current ideal/fseries catalogs:

```javascript
components: [{
  I: 1,
  L: 823.38,
  pointCount: 300,
  coeffs: [
    { I: 0, A: [/* x,y,z */], B: [0,0,0] },
    { I: 1, A: [/* x,y,z */], B: [/* x,y,z */] }
  ]
}]
```

The catalog entry is explicitly marked:

```javascript
ideal: false
status: "relaxed-candidate"
```

It also stores source SHA-256, checkpoint, normalization metadata, component lengths, edge statistics, bounding box, Fourier reconstruction error and an approximate/rounded pairwise Gauss-linking matrix.

## VortexLab integration status

`vortexring-lab-v7.6.24d` currently loads `ideal_knots_data.js` and `fourier_knots_data.js`, but it does not yet register `KNOTPLOT_KNOT_DB`.

The generated file is schema-compatible with the existing Fourier sampler. Integration requires:

1. Add this classic script after the other catalogs:

```html
<script src="./knotplot_knots_data.js" onerror="void 0"></script>
```

2. Register `KNOTPLOT_KNOT_IDS` / `KNOTPLOT_KNOT_DB` as a third catalog source and dropdown.

Do not label these KnotPlot candidates as globally ideal/tight without a separate convergence and ropelength certification.
