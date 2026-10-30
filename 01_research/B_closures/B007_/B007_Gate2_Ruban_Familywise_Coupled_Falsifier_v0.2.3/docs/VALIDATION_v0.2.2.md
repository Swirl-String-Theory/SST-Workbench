# Release validation — B007 v0.2.2

- 41/41 regression tests passed after all changes (see `tests/`).
- Tested CLI entrypoints: `--kind borromean`, `--family T_3_9`, `--external-source reference`, `--fit-mode compare`, `--fit-mode axial --fit-weighting vertex`, `--euler preview --background single`.
- Source audit confirmed all four BORRO family inputs; 1024/2048 are **source** variants for only two families.
- Sample runs use 128 filament points and 2 Heun steps; these are **smoke tests**, not research convergence runs.
- E010 parametric generator and original Borromean input files retained exactly; no library index or catalog mutation.
- Continuous 3D finite-core Euler equilibrium: UNRESOLVED.
