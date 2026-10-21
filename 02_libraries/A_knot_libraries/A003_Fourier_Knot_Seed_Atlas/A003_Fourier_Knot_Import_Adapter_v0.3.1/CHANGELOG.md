# A003 Change Log

## v0.3.1 — 2026-10-20 — Dynamic Topology & Spatial Convergence Qualification

- Preserves v0.3.0 G5/F3/F4 historical evidence and read-only E010/C005/Framework sources.
- Adds `g6_dynamic_qualification_v031.py` source-native evolving C005-RK4 path: F3/F4 × N150,300,600,1200; T=2; step schedules (4,8,16) and N1200 (8,16).
- Saves 40 actual evolving polygon snapshots with SHA256, independently computes minimum finite 3D segment distances, 2× snapshot-projection diagrams, Alexander determinants, fixed-reference pyknotid Alexander+v3 where available, explicit degeneracy screens.
- Adds Kabsch nonrigid RMS, centroid motion, length drift, spatial nested residuals/observed orders, independent per-mesh temporal halving at fixed final time.
- New v1.0.10 source-pinned diagnostic gates G6P10–P13. Physical G6, canonical E010 registry, and full Euler pressure-Poisson closure remain UNRESOLVED.
- Adds `g6_dynamic_replay_v031.py` for read-only SHA-verified v0.3.0 endpoint replay, marked HISTORICAL/DIAGNOSTIC_ONLY.
- Windows entrypoints `run_all.cmd G6`, `COMPLETE`, `G6_FULL`, `G6_LEGACY` and `run_g6_dynamic.cmd`.
- Existing G5 `QUALIFY` output is now stored in new v0.3.1 outputs root, accepted by G6 receipt discovery; historical g5 archives preserved.
- Adds `scipy>=1.10` dynamic dependency and independent brute-force segment-distance, 40-snapshot archive, and test-double guard regressions.
- No claimed canonical E010 modifications, knot identity theorem, collision-free homotopy proof, or physically calibrated continuum Euler model.
