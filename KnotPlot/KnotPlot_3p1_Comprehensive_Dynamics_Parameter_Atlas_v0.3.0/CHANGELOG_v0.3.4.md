# CHANGELOG v0.3.4 — Exact SST v0.4.8 Integration

## Grounded target

Default target path:

```text
C:\workspace\projects\SST-Workbench\SST_Trefoil_Lobe_Orientation_Blind_Falsifier\SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.8_Adaptive_Spectral_DD32_compact
```

The supplied v0.4.8 compact archive was inspected directly.
SHA-256 of the inspected archive:

```text
e59fbdde27a51da1dfda1a7980aff01150653dc1252f58eae1834204b582c921
```

Verified package version: `0.4.8`.

## Exact APIs used

The bridge does not shell-guess input syntax. It imports the actual v0.4.8 APIs:

- `sst_blind.multitopology.run_panel(...)`
- `sst_blind.spectral_extension.load_rung_by_source(...)`
- `sst_blind.spectral_extension.evaluate_triplet(...)`
- `sst_blind.spectral_extension.write_extension_outputs(...)`

Custom atlas geometries are supplied as `kind="knotplot"` XYZ inputs.

## Stability chain

### 1. CPU/FP64 screen
Config: `configs/panel_extended.json`

Tests the custom trefoils with the v0.4.8 generic TBK basis, short nonlinear
ringdown, RPO search and conditional Floquet gate.

### 2. Adaptive high-k DD32 linear closure
Uses the exact v0.4.8 N=720 sequence:

- k_max=16
- 24
- 32
- 48 only if unresolved
- 64 only if still unresolved

Only a `SPECTRAL_CONVERGED_K*` candidate with P2 growth verdict PASS can proceed
to confirmatory full dynamics.

### 3. CPU/FP64 R5 full-dynamics confirmation
Config: `configs/hr_ladder/05_R5_N720_K16_ROBUST_FULL.json`

This evaluates the promoted candidates at N=720 with k<=16, the robust epsilon
ledger, nonlinear ringdown and RPO/Floquet diagnostics.

### 4. Synthesis

Creates:

- `analysis/SST_V048_STABILITY_MATRIX.csv`
- `analysis/SST_V048_STABILITY_MATRIX.md`

## Important normalization fact

v0.4.8's `normalize_components` rescales every input geometry to total arclength
`2*pi`. Therefore this bridge tests normalized **shape dynamics**, not absolute
KnotPlot size/scale dependence.

## Gate policy

v0.4.8 itself defines P0/P1/P2/P5 as the critical full-dynamics gates.
P7 RPO recurrence and P8 Floquet boundedness are retained separately as
diagnostic evidence and are not silently made critical by the bridge.

## Commands

Fast physical screen only:

```bat
run_sst_stability_screen.cmd
```

Full chain:

```bat
run_sst_stability_all.cmd
```

If DD32 is unavailable, use:

```bat
run_82b_sst_v048_spectral_fp64.cmd
```

then continue with `run_83_sst_v048_confirm_fp64.cmd` and
`run_84_sst_v048_synthesize.cmd`.
