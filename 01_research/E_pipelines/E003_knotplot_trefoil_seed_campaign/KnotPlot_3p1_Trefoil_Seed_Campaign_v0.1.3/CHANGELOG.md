# CHANGELOG

## v0.1.3 — literal KPC syntax correction

- Recovered exact syntax from user's working `build_knot_0.1.kpc`.
- `nbeads 300` -> `refine nbeads 300`.
- Removed target-unknown `charge`, `hooke`, `power`, `timeincr`.
- Added strict generated-KPC syntax audit before relaxation.
- 38 preregistered seed geometries unchanged.


## v0.1.2 — output-directory hotfix

- Create parent directories for every KnotPlot `save`/`coords` target before execution.
- Add runtime-directory `.keep` files so ZIP extraction preserves the folder tree.
- No change to the 38 frozen seeds or relaxation protocol.


## v0.1.1 — target KnotPlot runtime hotfix

- Removed `alex -1`; target installation has no `KP-alex.exe`.
- Topology runtime diagnostics are now `safe`, `dowker`, `lnknum`.
- Startup `nothing loaded/save/output` pre-banner noise is not considered fatal
  when all expected files exist.
- 38 seed definitions and fixed relaxation protocol are unchanged.
- v0.1.0 failed before base export, so no production endpoint was observed.


## v0.1.0 — prospective trefoil seed campaign

- Replaces preparation-parameter replication with 38 preregistered start embeddings.
- Uses the installed KnotPlot `load 3.1` geometry as the parent curve.
- Adds closed Bishop-frame helical and mixed-mode seed perturbations.
- Adds six invertible PCA-axis affine seed embeddings.
- Adds vectorized dense-curve straight-line homotopy clearance gate.
- Uses one fixed M+E+B relaxation protocol for every seed.
- Saves `i00000`, `i01000`, `i04000`, `i10000` `.k` and coordinate files.
- Retains KnotPlot topology diagnostics in per-seed logs.
- Audits identity128 duplicates and historical-v0.1.7 novelty64 before handoff.
