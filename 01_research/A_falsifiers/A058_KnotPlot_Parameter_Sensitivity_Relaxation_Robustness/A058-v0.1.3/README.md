# A058 v0.1.3 — KnotPlot Parameter Sensitivity & Relaxation Robustness

Framework pin: **SST Falsifier Framework v1.0.6** (`cpu` profile).

This falsifier answers two separate questions:

1. Does KnotPlot relaxation materially bias the exported geometry as its settings change?
2. Even if the geometry is robust, are the historical export scripts provenance-complete enough to serve as canonical SST geometry data?

The uploaded historical script set is included unchanged under `inputs/original_scripts/`.

## Recommended run order

```bat
run_install.cmd
run_10_prepare_campaign.cmd smoke
run_all.cmd SELFTEST C:\workspace\projects\SST-Workbench
run_all.cmd FREEZE   C:\workspace\projects\SST-Workbench
run_20_run_knotplot.cmd smoke
run_all.cmd FULL C:\workspace\projects\SST-Workbench
```

Then run the pilot:

```bat
rem For the definitive pilot, regenerate the pilot scripts BEFORE a fresh FREEZE/versioned run.
run_10_prepare_campaign.cmd pilot
run_all.cmd FREEZE C:\workspace\projects\SST-Workbench
run_20_run_knotplot.cmd pilot
run_all.cmd FULL C:\workspace\projects\SST-Workbench
run_all.cmd REVEAL_IF_ALLOWED C:\workspace\projects\SST-Workbench
```

`run_pilot_all.cmd` now works without a KnotPlot path when the supplied workstation layout is present. Optional positional arguments remain `<knotplot.exe> <SST-Workbench-root> <start-in>`.

KnotPlot executable resolution order is: explicit argument, `KNOTPLOT_EXE`, `%USER_PROFILE%\AppData\Local\Programs\KnotPlot\KnotPlot.exe`, then the standard Windows `%USERPROFILE%` equivalent. Start-In resolution is: explicit argument, `KNOTPLOT_STARTIN`, `%SST_WORKBENCH%\04_tools\A_geometry\A001_knotplot\` (or inferred Workbench root), then the A058 output directory as a safe fallback. Passing `outputs` as argument 3 explicitly selects the output directory.

Campaign scripts are generated **before** protocol freeze and now contain absolute paths for their own CSV/ASCII outputs. Therefore changing KnotPlot Start-In cannot redirect campaign evidence accidentally. Runtime provenance records the resolved executable path, executable SHA-256, and Start-In directory in `campaign/runtime_<tier>.json`.

## Important interpretation rule
A KnotPlot/Ridgerunner relaxed curve is a geometry candidate. A058 does **not** promote relaxation to physical self-confinement or SST particle stability.

## Canonical replacement export contract
Any later production exporter should:
- explicitly use `save ... ascii` (or another explicitly declared format);
- write per-checkpoint metrics to CSV;
- retain the exact script, configuration, KnotPlot build identifier, and SHA-256;
- record KnotPlot `version` plus the full `parameters` state and explicitly pin every relaxation-relevant default promoted to production;
- keep analytic/initial and relaxed checkpoints in one lineage;
- use A058's qualified parameter envelope instead of an inherited single setting.

### v0.1.3 FREEZE/blindness hardening

The canonical Framework-v1.0.6 generator invariant is now present: `private/OPAQUE_ID_KEY.bin` and `private/REVEAL_NONCE.bin` are exactly 32 bytes and are verified before FREEZE. Generated KnotPlot `.kpc` execution scripts and raw KnotPlot logs remain under `private/` because they contain construction commands; public campaign manifests/results use only anonymous `Txx`/`Cxxxx` identifiers.
