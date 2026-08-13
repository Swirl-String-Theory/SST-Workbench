---
name: Batch catalog VortexLab
overview: "Vervolg: na batch polish automatisch VortexLab-uniform N=300 + catalog_status + upsert naar knotplot_knots_data.js."
todos:
  - id: post-polish-hook
    content: "Per succesvolle stem: resample polish → uniform N300 + classify_catalog_status (zelfde pad als run_build -rr stage 4)"
    status: pending
  - id: upsert-batch
    content: "Batch upsert via build_knotplot_knots_data.py --from-rr-outdir; summary welke ids updated"
    status: pending
  - id: flags
    content: "--catalog-upsert / --no-catalog op run_catalog_batch; default off tot betrouwbaar"
    status: pending
  - id: tests
    content: Unit tests hook + dry upsert; full suite before/after
    status: pending
dependsOn: fseries_batch_ladder_94660855
isProject: false
---

# Vervolg: auto catalog upsert / VortexLab

**Depends on:** [fseries_batch_ladder_94660855](fseries_batch_ladder_94660855.plan.md). Optioneel na [knotplot_export_batch_followup](knotplot_export_batch_followup.plan.md) voor KnotPlot ids.

## Goal

`run_build.cmd -rr` schrijft na polish een VortexLab-uniform N=300 en upsert naar `knotplot_knots_data.js`. De fseries/catalog batch doet dat nu niet. Dit plan koppelt dezelfde post-steps aan batch-success.

## Approach

- Hergebruik: `resample_closed_knot_txt.py --points 300`, `classify_catalog_status.py`, `build_knotplot_knots_data.py --from-rr-outdir`.
- Input polish: kies canonieke N (waarschijnlijk N300 polish of hoogste gevraagde N — **vastgelegd bij implementatie als N300 VortexLab-copy**, consistent met huidige `-rr`).
- Flag default **off** (`--catalog-upsert` om aan te zetten) tot metrics/gates stabiel zijn.
- Geen `certified-ideal` automatisering.

## Verification

- Unit tests met temp outdir + fake polish metrics
- Smoke één stem met `--catalog-upsert`; diff op catalog entry
