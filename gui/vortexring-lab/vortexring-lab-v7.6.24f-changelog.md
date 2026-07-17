# VortexLab v7.6.24f

Base: v7.6.24e1  
Scope: KnotPlot catalog integration and `Tlink_6_9` benchmark holdout.  
Solver physics: unchanged.

## Added: third external geometry catalog

VortexLab now optionally loads:

```html
<script src="./knotplot_knots_data.js" onerror="void 0"></script>
```

A separate **KnotPlot relaxed candidates** dropdown is available in the VORTEXKERN/configuration panel. It is intentionally separate from:

- Brian Gilbert ideal/tight data;
- compact `.fseries` data.

KnotPlot entries retain their source status and warning. They are not relabeled as globally ideal, tight, or ropelength-minimizing.

## Added: `Tlink_6_9`

The supplied catalog registers:

- key: `Tlink_6_9`;
- source: `Tlink_6_9_D1_040k.txt`;
- checkpoint: 40,000 relaxation steps;
- status: `relaxed-candidate`;
- family: torus link `T(6,9)`;
- three components;
- each component topologically `T(2,3) / 3_1`;
- rounded pairwise linking matrix with off-diagonal value `-6`;
- 300 source points per component;
- full discrete Fourier spectrum.

The generated catalog stores SHA-256 provenance, source normalization metadata, component lengths, bounding box, Fourier reconstruction error and approximate Gauss-linking diagnostics.

## Main UI

The new KnotPlot dropdown can load the complete three-component object. Existing component controls remain available:

- **Volledig catalogusobject** loads all three components per carrier;
- **Eén component isoleren** allows individual component inspection.

The info panel distinguishes:

- `Ideal`;
- `Fseries`;
- `KnotPlot`.

## Swirl Clock benchmark selector

The holdout selector now has three source checkboxes:

- Ideal;
- Fseries;
- KnotPlot.

The multi-select list includes:

```text
T(6,9) · 3-componentenlink · KnotPlot
```

A dedicated preset was added:

```text
Link · T(6,9)
```

This preset selects only the KnotPlot source and only `Tlink_6_9`.

The **Volledig** preset includes `Tlink_6_9` in addition to the existing knot set.

## Tlink benchmark definition

The Tlink holdout uses:

- all three link components for carrier A;
- all three link components for carrier B;
- `N = 128` points per component;
- 768 dynamic centerline points in total across both carriers;
- checkpoints at `t = 0` and `t = 3 s`;
- canonical transverse RMS radius `0.05 m`;
- intrinsic `Ω_parallel` analysis;
- `a_sim = 0.1 mm`.

The smaller numerical regularization is deliberate. At the canonical RMS scale, the D1 component separation is approximately `0.70 mm`. The topology-guard threshold is then:

```text
3 a_sim = 0.30 mm
```

This avoids an artificial t=0 guard collision while keeping `a_sim` explicitly numerical. It does not identify the KnotPlot D1 normalization with a physical SST core radius.

## Scientific boundary

`Tlink_6_9` is an additional relaxed-candidate holdout. It:

- does not train or select a `κ_geom` factor;
- does not receive an ideal ropelength from another embedding;
- does not treat KnotPlot `D1` metadata as a certified physical tube diameter;
- participates in no-fit candidate screening and intrinsic-rotation diagnostics;
- remains separate from Fourier/ideal embedding-pair comparisons because no matched ideal/Fourier `T(6,9)` pair is registered.

The torus-link crossing count used by the existing crossing-number diagnostic is `45`, from the standard positive torus-link diagram count `min((p-1)q,(q-1)p)` for `p=6`, `q=9`. Reach-dependent conclusions remain blocked until v7.6.25 supplies the continuous DCSD/reach solver.

## Tooling included

The package includes:

- `knotplot_knots_data.js`;
- `build_knotplot_knots_data.py`;
- `KNOTPLOT_KNOTS_DATA_README.md`.

The builder can update the stable `Tlink_6_9` entry from later checkpoints without hand-editing the JavaScript catalog.

## Validation

Passed:

- inline JavaScript syntax;
- KnotPlot catalog JavaScript syntax;
- converter Python syntax;
- unique static DOM IDs;
- required UI controls;
- `Tlink_6_9` metadata and linking matrix;
- canonical-scale D1/topology-guard margin;
- KnotPlot scenario/source wiring;
- prevention of false ideal-ropelength derivation;
- byte-identical `velocityCore`, `velAll`, `rk4Step`, and `topologyClearance` functions relative to v7.6.24e1.

A complete interactive WebGL `Tlink_6_9` run was not executed in the container. The first local check should use **Link · T(6,9)** followed by **Geselecteerde holdouts**.
