# CHANGELOG v0.3.3 — Shape-Canonical + SST Bridge

## Why this release exists

The i=1000 atlas shows persistent and often growing preparation sensitivity.
In particular the reported indexed RMS is very large for `tanforce`/`tanmag`.
Indexed RMS can confuse bead sliding along the same closed curve with genuine
shape change.

## New shape-canonical gate

Adds `shape_canonical_analysis.py`:

1. correct row-vector Kabsch convention:
   `H=A.T@B`, `R=U@Vt`, proper rotation only;
2. uniform closed-curve arclength resampling to N=300;
3. cyclic phase minimization after resampling;
4. orientation reversal is NOT allowed;
5. reports both indexed RMS and shape RMS;
6. classifies parameter families as geometry-dominant vs.
   reparameterization-dominated.

Outputs:
- `analysis/SHAPE_CANONICAL_EXTENDED.md`
- `analysis/SHAPE_CANONICAL_EXTENDED.json`
- `analysis/SHAPE_CANONICAL_EXTENDED.csv`
- pairwise diagnostic CSV.

## SST stability handoff

Adds `prepare_sst_stability_handoff.py`.

It stages:
- exact raw KnotPlot XYZ;
- uniform-arclength N=300 XYZ with original scale preserved;
- exact SHA-256 provenance;
- baseline detection;
- full effective-family manifest;
- screening manifest using extrema/default/max-shape-pair representatives.

The handoff is explicitly preparation data; it does not label a geometry stable.

## Requested downstream

Target:
`SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.8_Adaptive_Spectral_DD32_compact`

The exact v0.4.8 compact package/interface was not available when this release
was built. Therefore v0.3.3 does not guess its CLI. Instead,
`discover_sst_v048_interface.py` searches the local SST-Workbench workspace and
writes the actual entry-point/interface inventory.

This prevents silently feeding geometry into the wrong command/configuration.

## Resume

After a completed v0.3.2 extended campaign, run only:

`run_reanalyze_shape_and_prepare_stability.cmd`

No KnotPlot relaxation rerun is required.
