# Expected import for a future true 3D PKLSA source

Provide `native_omega.npz` with `omega` array shaped `(3,N,N,N)` in physical or dimensionless coordinates, finite float64 values. Or export `u`/`p` also in a separately versioned source. The source must have a JSON sidecar: `schema`, `source_sha256` of the NPZ, `provider`, `run_id`, `solver_commit`, `boundary_conditions`, `time`, `units`, `source_class`, `independence_group`. Set `source_class=SOURCE_NATIVE_DYNAMICAL_SNAPSHOT` only for a genuinely simulated 3D dynamic field. For a claim of independent heldout u/p, use separate upstream origin metadata and source hashes, not the synthetic FFT reconstruction.

To inspect metadata and shape without certification: `run_all.cmd CORE3D_IMPORT path\native_omega.npz path\manifest.json` (CURRENT importer only verifies fields and hash; it does not grant a physical PASS).
