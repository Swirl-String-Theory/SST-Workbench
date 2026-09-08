# Reproducibility Policy — v0.4.5.3 compact archive

## Principle

Scientific reproducibility is preserved without recursively embedding every maintenance ZIP. Runtime-only releases do not justify duplicating the entire prior history.

## Embedded scientific capsule

`release_history/SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.1.zip` is retained byte-for-byte. That ZIP already contains the exact v0.1.0, v0.1.1, v0.2.0, v0.3.0 and v0.4.0 ZIPs. `release_history/INDEX.sha256` verifies the embedded capsule.

`release_history/HISTORICAL_HASHES.sha256` records hashes of historical standalone releases, including omitted runtime-only v0.4.2–v0.4.5.2 artifacts.

## Why v0.4.1 is the capsule boundary

v0.4.1 introduced the 127-object complete Fremlin + KnotPlot/RidgeRunner archive campaign and froze the scientific FULL/EXTRA_EXTENDED configs. v0.4.2–v0.4.5.2 changed Windows/SYCL loading, worker lifecycle, progress reporting and packaging only; they did not alter scientific gate semantics or preregistered thresholds.

## Input preservation

The release still contains:

1. exact canonical panel inputs under `repro_inputs/panel/`;
2. complete `Fremlin_Knots_FourierSeries.zip`;
3. complete `KnotPlot_RidgeRunner_Knots_Links.zip`;
4. legacy trefoil files required by v0.1–v0.3.

## Historical recomputation

```bat
run_reproduce_history_basic.cmd
run_reproduce_history_extended.cmd
```

The reproduction tool unwraps the v0.4.1 capsule into `_history_work/`, then uses the exact nested historical ZIPs for v0.1–v0.4.0. Temporary extraction is not part of the distributed release.

## Current campaigns

Canonical panel:

```bat
run_panel_basic.cmd
run_panel_extended.cmd
```

Full archive:

```bat
run_archive_validate.cmd
run_archive_extra_extended.cmd
run_archive_full.cmd
```

The validated inventory remains 78 Fremlin `.fseries` + 49 KnotPlot/RidgeRunner finals = 127 geometries.

## Reference snapshots

Only summary-level validated reference material is packaged. Bulky per-blind-object historical analysis JSON files are omitted because they are recomputable from the scientific capsule and preserved inputs. Reference snapshots are never read by scoring code.

## Resume semantics

Existing output directories are resumed only when their parsed preregistered configuration equals the requested configuration. This prevents mixing thresholds or resolutions across runs.
