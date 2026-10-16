# A058 KnotPlot Parameter Sensitivity & Relaxation Robustness — v0.1.4

**Status:** recovery analysis of the completed v0.1.3 pilot. No KnotPlot rerun is required.

v0.1.3 successfully executed all 150 KnotPlot conditions and produced all 900 ASCII coordinate checkpoints, but its FULL analysis failed because it repurposed Framework-v1.0.6 gate G6 (reserved for GPU screening) and because all KnotPlot `metrics.csv` files were zero bytes.

v0.1.4 repairs the analysis without mutating v0.1.3:

- imports the public v0.1.3 campaign read-only;
- fixes G4/G5/G6/G7 to Framework-v1.0.6 semantics;
- uses coordinate-derived FP64 metrics and the already preregistered `D_shape` thresholds;
- records zero-byte KnotPlot CSV logs as missing;
- fixes Workbench-relative source-contract paths;
- preserves anonymous Txx identities until reveal.

## Run

From `A058-v0.1.4`:

```bat
run_recover_v013.cmd
```

Default source:

```text
..\A058-v0.1.3
```

Or pass the v0.1.3 outputs ZIP explicitly:

```bat
run_recover_v013.cmd "C:\path\A058_KnotPlot_Parameter_Sensitivity_Relaxation_Robustness_Falsifier_v0.1.3-outputs.zip"
```

The command installs/builds the native CPU lane, imports and hashes the prior acquisition, runs SELFTEST/FREEZE, and executes FULL analysis. It does **not** invoke KnotPlot.

## Scientific boundary

A relaxed KnotPlot embedding is a geometry candidate, not evidence of SST dynamical stability. v0.1.4 is a recovery/reanalysis of existing simulation data and is not an independent confirmation source.
