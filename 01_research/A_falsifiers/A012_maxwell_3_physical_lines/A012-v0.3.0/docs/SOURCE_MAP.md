# Source map

- Historical motivation: J. Clerk Maxwell, *On Physical Lines of Force*, Plate VIII Fig. 1 and accompanying Part II text.
- Geometry/provenance authority: local E010 PKLSA `v0.3.x`, newest production release unless explicitly pinned.
- E010 loader authority: `pklsa_builder.io_geometry.load_geometry`.
- E010 source integrity: carrier raw SHA-256 + `geometry_sha256`.
- Topological target: E010 exact polygonal linking kernel (`pklsa_builder._native.linking_number_exact`) with a mathematically equivalent Python solid-angle fallback.
- Dynamical observable: this package's independent `cpp/native.cpp` Biot--Savart/circulation kernel.
- The files in `docs/upstream_reference/` are audit snapshots of the inspected E010-v0.3.1 release metadata, not runtime replacements for the live Workbench.
