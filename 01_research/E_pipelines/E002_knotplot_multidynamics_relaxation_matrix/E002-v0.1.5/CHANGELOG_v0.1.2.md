# CHANGELOG — patch v0.1.2

- Clarified scientific split: 3.1 matrix = parameter-effect discovery; catalog = later propagation.
- Corrected target-runtime bead command to `refine nbeads N`.
- Removed `alex -1` from matrix checkpoints because target runtime lacks KP-alex.exe.
- Added strict static/log/output audit; KnotPlot exit code 0 is no longer sufficient for PASS.
- Existing outputs are archived before a fresh discovery campaign.
- Added machine-readable `matrix_design.json`.
- Added geometry-effect analysis and duplicate-geometry flags.
- Added explicit, initially unapproved `catalog_recipe.json`.
- Catalog conversion now injects recipe commands and embeds recipe SHA-256.
- Added recipe selection helper and strict catalog batch runner.
- Catalog is no longer implied by `run_all.cmd`; it requires explicit preparation/approval.
