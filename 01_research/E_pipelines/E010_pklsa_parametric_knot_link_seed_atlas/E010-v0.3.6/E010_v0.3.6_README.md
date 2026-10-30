# E010 v0.3.6 — Ruban Torus Knot/Link Geometry Atlas

**Status:** `DEVELOPMENT_GEOMETRY_ONLY` — no filament or 3D Euler dynamics have been run in this release; no stable seed or relative equilibrium is claimed.

This is an **additive subfamily** of the E010 parametric knot/link seed atlas. It does not replace the authoritative E010 manifest or modify the older v0.3.5 release. Do not promote these geometries into a production topology atlas without independent qualification.

## What is included

- **24 knot embeddings**, including `T_2_9` and `T_2_11`, plus **6 torus link families** (`T_3_3`, `T_3_6`, `T_3_9`, `T_6_9`, `T_6_15`, `T_6_21`).
- Each of the six link families has **three independent, closed components** (`_C00`, `_C01`, `_C02`). They are not one triple-traced curve.
- A complete fine atlas: **121 B0 values from 0.02 to 0.32 inclusive at intervals of 0.0025**; 3,630 nominal geometries, 3,630 perturbed geometries, 10,164 coordinate files, 1024 sample points **per component**.
- **54,450 proposed** scenarios: five Lambda values times three delta/R0 values per nominal geometry. All are `NOT_RUN`.
- Both nominal and perturbed versions. The perturbation is a **global, smooth, volume-preserving diffeomorphism**, shared by all components of a link; topology is conserved in the underlying continuous analytic construction. Polygonal sampled-curve topology has not been independently certified for all 7,260 geometries.
- Machine-readable `FAMILY_INDEX.json`, `BUILD_SUMMARY.json`, `DYNAMICS_PENDING.json`, `GEOMETRY_VS_SURVIVAL.csv`, plus per-file SHA-256 hashes.

## Important provenance distinction

The new torus knot/link **coordinates are analytically generated** with the torus parameterization. KnotPlot/VortexLab names for the six three-component links are retained as catalog *references* with the historical `stalled-not-converged` tag; their native KnotPlot coordinate datasets were **not imported**. All generated coordinates form **one analytic source group**, not multiple independent datasets.

For link components, `g = gcd(p,q)`, each component is parameterized with winding `(p/g, q/g)` and a distinct meridional phase. Expected pairwise linking is `pq/g^2`.

## Installation and regeneration (Windows)

```bat
py -m pip install -r requirements.txt
py -m unittest discover -s tests -v
py build_ruban_family.py --mode pilot --output-root ..\E010_v036_pilot_rebuild
py build_ruban_family.py --mode fine --output-root ..\E010_v036_fine_rebuild
```

Use `run_all.cmd` to regenerate the fine release from scratch **only in a new location where the output folder does not already exist**. The generator intentionally refuses to overwrite existing outputs; use `--output-root` for an independent rebuild. `run_all_pilot.cmd` regenerates the 16-point B0 pilot scan in its own directory.

There is no requirement to rerun the full geometry generation just to inspect the distributed outputs. The delivery is split into `E010_Ruban_Torus_Dynamics_Family_v0.3.6_core.zip` and **seven** `E010_v0.3.6_KNOTS_*.zip` / `E010_v0.3.6_LINKS_*.zip` shards to accommodate transfer limits. Extract every archive into the SAME parent folder (or use `assemble_atlas.ps1`). The core contains the full scenario index and per-file hashes; the shards contain all 10,164 XYZ files.

## Data interpretation

`B0=r0/R0` is the torus minor-to-major radius ratio. It is **not** the physical finite-core radius and is **not** a spatial-grid resolution. `Lambda=ln(R0/xi)` specifies a potential regularization scale. `delta_over_R0` is a separate scenario parameter; neither parameter was evolved in this geometry-only release. Distinguish this `point_count=1024` from the 3D fluid grid size. No dynamic equilibrium/stability or continuum reach certification is included.

## Validation

Run the 15 included regression tests, then check every line of `MANIFEST_SHA256.txt` in the separate fine outputs. All source and output archive SHA-256 files accompany their ZIPs.
