# KnotPlot Parameter Atlas v0.3.4 — SST v0.4.8 Integrated Stability

This release closes the loop:

```text
KnotPlot parameter
    ↓
relaxed trefoil at i=1000
    ↓
shape-canonical dedupe
    ↓
SST v0.4.8 TBK/RPO/Floquet screen
    ↓
adaptive N=720 high-k spectral convergence
    ↓
CPU/FP64 full-dynamics confirmation
    ↓
parameter -> physical stability matrix
```

Default v0.4.8 project:

```text
C:\workspace\projects\SST-Workbench\SST_Trefoil_Lobe_Orientation_Blind_Falsifier\SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.8_Adaptive_Spectral_DD32_compact
```

Override without editing scripts:

```bat
set SST_V048_DIR=C:\some\other\v0.4.8_folder
```

## Recommended usage on the existing working atlas folder

You already have the KnotPlot i=1000 outputs. Overlay the v0.3.4 patch and run:

```bat
run_dry.cmd
run_reanalyze_shape_and_prepare_stability.cmd
run_sst_stability_all.cmd
```

The last command is potentially expensive.

For a cheaper first look:

```bat
run_sst_stability_screen.cmd
```

This runs only the CPU/FP64 `panel_extended` TBK/RPO/Floquet screen.

## Full-chain meaning

A candidate is not called stable merely because KnotPlot converged.

The bridge separates:

- `LINEAR_UNSTABLE_SPECTRALLY_CONVERGED`
- `SPECTRAL_UNRESOLVED`
- `SPECTRALLY_BOUNDED_AWAITING_FULL_DYNAMICS`
- `FULL_DYNAMICS_FAIL`
- `FULL_DYNAMICS_PASS_NO_RPO_RECURRENCE`
- `FULL_DYNAMICS_PASS_RPO_FOUND_FLOQUET_NOT_BOUNDED_OR_NOT_EVALUATED`
- `FULL_DYNAMICS_PASS_RPO_FLOQUET_BOUNDED`

The strongest result available from this chain is therefore:

```text
spectrally converged P2 PASS
+ CPU/FP64 P0/P1/P2/P5 PASS
+ RPO recurrence found
+ Floquet non-neutral spectral radius within the v0.4.8 bound
```

P7/P8 remain diagnostic under the native v0.4.8 gate policy.

## Scale warning

The v0.4.8 multi-topology loader resamples and rescales every geometry to total
length 2π. Absolute KnotPlot scale is intentionally factored out. This is a
normalized shape-stability comparison.
