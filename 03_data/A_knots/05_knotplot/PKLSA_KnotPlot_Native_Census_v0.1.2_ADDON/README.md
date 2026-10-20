# PKLSA E010 v0.3.1 — KnotPlot Native Census v0.1.2 ADDITIVE provider

## Purpose

**Opt-in only.** Installs a new, versioned KnotPlot baseline dataset, preserving all existing KnotPlot, PKLSA and legacy data. Does not edit `sst_pklsa/core.py`, change default dataset selection, rewrite historical release outputs or alter A001-A008 producer catalogue IDs.

**Source:** the user's `KnotPlot_falsifier_census_v0.1.2.zip` raw files, cross-checked with the `KnotPlot_Census_v0.1.2_VERIFIED_AUDIT.zip` registry. 20 knots, 16 links, 14 torus objects; 85 loops, 4,431 beads. KPF and high-precision XYZ are preserved byte-identically.

## Destination

`SST-Workbench/03_data/A_knots/04_knotplot/PKLSA_KnotPlot_Native_Census_v0.1.2/`

The install also creates an **optional** source record in E010 v0.3.1 `configs/source_contract_v1.json` and `source_contract_production_v2.json` when available and adds `sst_pklsa/knotplot_census.py` as a separate module. Existing contract files receive backups; on a second run the installer checks content and is idempotent. No existing geometry files will be overwritten.

## Install on Windows

Extract this entire ZIP into a temporary folder, run `INSTALL.cmd`. It assumes the Workbench location `C:\workspace\projects\SST-Workbench`.

Or call explicitly:

```
py -3 install_additive.py --workbench C:\workspace\projects\SST-Workbench
py -3 verify_dataset.py --dataset C:\workspace\projects\SST-Workbench\03_data\A_knots\04_knotplot\PKLSA_KnotPlot_Native_Census_v0.1.2
```

If E010 is at a different path:

```
py -3 install_additive.py --workbench C:\workspace\projects\SST-Workbench --pklsa C:\workspace\projects\SST-Workbench\01_research\E_pipelines\<your E010 folder>\E010-v0.3.1
```

`--data-only` installs the dataset without touching the E010 provider contracts. This is useful if E010 is frozen/archived and a separate minor version must be made first.

## Consumption from existing falsifiers

```
from sst_pklsa import Workbench
from sst_pklsa.knotplot_census import KnotPlotNativeCensus, DATASET_ID

wb = Workbench.open(r"C:\workspace\projects\SST-Workbench")
census = KnotPlotNativeCensus.open(wb)  # explicit opt-in
print(DATASET_ID)
print(census.list_ids(kind="knot"))
points_by_component = census.load("knot_3.1")
print(census.provenance("knot_3.1"))

# Link: retains component segmentation and ordering, NOT one flattened bead chain
loops = census.load("link_6.3.3")
```

For legacy tests that want file paths rather than arrays, use `census.xyz_path("torus_6.21")`. The public API returns NumPy `Nx3` arrays in a list, consistent with `pklsa_builder.io_geometry.load_geometry`.

**Selection policy:** do not add the census to default provider enumerations, publication claims or independent source counts. The source contract has `admit_geometry=false` (no automatic admission). Falsifiers may explicitly use the coordinates with a pinned dataset ID and hashes as **unqualified geometry**, reporting native KnotPlot units. Historical baselines remain unchanged. Full topology identity and finite-core convergence are separate qualification gates.

## Scientific limits

- These are discrete polygonal centreline geometries; not automatically finite-core vortex configurations.
- `L` is in native KnotPlot coordinate units. Never interpret as meters without an explicit transformation.
- Torus geometries are procedure-generated and not necessarily equivalent to a catalogued, verified knot identity; keep naming and original component structure, no guessed crosswalk.
- Geometry parity `PASS` ≠ topo identity or dynamic stability `PASS`.
- Polygonal length derived from `.kpf` FP32 coordinates; the accompanying ASCII may deviate in the low 1e-6 coordinate range, hence length tolerance <3e-4 native units.
- The new dataset reuses KnotPlot source methodology; **not independent from older KnotPlot providers**.

## Rollback

Remove the new dataset directory, the new `sst_pklsa/knotplot_census.py`, and the optional source entry with ID `knotplot.native_census.v0.1.2` from PKLSA configuration JSONs, or restore the adjacent `.before_knotplot_native_v012.bak` files if no other edits happened afterward. Do not delete the original provider folders.
