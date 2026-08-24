# v0.3.3 Shape-Canonical + SST Stability Bridge

This release is designed to be overlaid on the existing atlas folder that
already contains the successful v0.3.2 `out\extended` results.

Run:

```bat
run_reanalyze_shape_and_prepare_stability.cmd
```

It does **not** rerun the 174 extended KnotPlot candidates.

The chain is:

```text
existing i01000 geometries
   -> corrected indexed Kabsch
   -> uniform-arclength N=300
   -> cyclic phase alignment
   -> genuine-shape ranking
   -> exact geometry dedupe
   -> SST screening/full handoff manifests
   -> discover exact v0.4.8 compact interface
```

Key files:

```text
analysis\SHAPE_CANONICAL_EXTENDED.md
stability_handoff\stability_candidates_screen.csv
stability_handoff\stability_candidates_full.csv
stability_handoff\handoff_manifest.json
analysis\SST_V048_DISCOVERY.md
```

## Physical stability policy

KnotPlot relaxation sensitivity is not physical vortex stability.

The intended downstream stability decision belongs to:

`SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.8_Adaptive_Spectral_DD32_compact`

The handoff preserves raw scale and also supplies an arclength-uniform copy.
No geometry is declared stable before the downstream TBK/RPO/spectral gates pass.

## Automatic v0.4.8 execution

Not enabled in this release because the exact v0.4.8 compact package was not
available to inspect. The discovery script searches the user's SST-Workbench
for that exact directory and inventories real `.cmd`/`.py` entry points.
Once the package/archive is available, the runner can be wired against its
actual input contract rather than guessed.
