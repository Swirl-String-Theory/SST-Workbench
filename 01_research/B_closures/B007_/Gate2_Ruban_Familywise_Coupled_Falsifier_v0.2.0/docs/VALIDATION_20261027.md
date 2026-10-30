# Validation run — 2026-10-27

- `python -m pytest -q tests`: **22 passed**.
- E010 v0.3.6 byte parity: `T_2_3_B2000_N1024.xyz` from the analytically regenerated v0.2.0 geometry is exactly byte-identical to the existing E010 KNOTS_01 atlas export. Matching SHA-256: `ace0cdc3a3bebde35c80b0bb07db1e014957fc4c864455819d80658fa97fcd23`.
- `--family all --profile fine --dry-run`: 30 families × 121 B0 × 5 Lambda × 2 perturbation states = 36,300 nominal/perturbed reduced filament simulations (dry-run only).
- `--topology 3_1 --profile pilot --dry-run`: 2 embeddings × 16 B0 × 5 Lambda × 2 = 320 runs (dry-run only).
- `--kind links --profile pilot --dry-run`: 6 families × 16 B0 × 5 Lambda × 2 = 960 runs (dry-run only).
- Actual `release_pilot_v020`: 16 geometry seeds, 160 reduced filament runs, 1 coupled periodic Euler pilot (numerical preflight BLOCKED). 0 / 80 paired B0/Lambda samples spatially eligible with 128-point screen. G3 selected diagnostic B0=0.32, Lambda=7 with explicit `PROVISIONAL_SPATIALLY_UNRESOLVED` and 2048/4096-point geometry exports.
- Actual `release_highres_v020`: 2 geometry seeds, 4 reduced filament runs at N1024 with Lambda=3.4, 2/2 sampled pairs passed spatial SCREEN heuristic. Selection B0=0.20, Lambda=3.4; 512 -> 1024 filament score change about 1.62%, still NOT convergence proof. Exported 2048/4096-point nominal + perturbed geometry.
- Actual `release_link_v020`: T(3,6) three-component link, two B0, 4 reduced filament runs and three separately exported component curves at 2048 points, G4 deliberately disabled.
- Each run has `MANIFEST_SHA256.json`, `FALSIFIER_REPORT.md` and a two-page `FALSIFIER_REPORT.pdf`, validated by raster rendering; all completed per-run ZIP archives pass `ZipFile.testzip()`.
- All results scientific status: `G2_UNRESOLVED_NO_CERTIFIED_EQUILIBRIUM`.

**NOT DONE:** full-field equilibrium optimization, independently validated 3D Euler spatial/time convergence, material topology certification, and a valid geometry-resolved large background network. The pilot G4 is an actual coupled Euler solver but it remains exploratory.
