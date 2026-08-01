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
