# Windows batch guide — v0.4.0

Open PowerShell or Command Prompt in the unpacked package directory.

## 1. Install

```bat
batch\01_setup_venv.bat
```

## 2. Test the extractors

```bat
batch\30_iso_gamma_area_selftest.bat
```

Expected: synthetic phase and period checks pass.

## 3. Run the positive control

```bat
batch\31_run_C9_positive_control.bat
```

Expected:

\[
\mathcal Q_\Gamma\simeq1.
\]

This proves the measurement pipeline can recover solid-body rotation.

## 4. Run the physical hole-contained falsifier

```bat
batch\32_run_C9_iso_gamma_area_smoke.bat
```

The script runs the campaign and analyzer. Results are written to:

```text
outputs\C9_iso_gamma_area_smoke\
```

The key files are:

```text
campaign_summary.csv
campaign_results.json
analysis\ISO_GAMMA_AREA_ANALYSIS.md
analysis\falsification_ledger.csv
analysis\iso_family_summary.csv
```

## 5. Run the research ladder

```bat
batch\33_run_C9_iso_gamma_area_research.bat
```

This compares:

- trefoil and mirror trefoil;
- positive and negative circulation;
- two mean-vorticity families;
- four bundle radii;
- two resolutions;
- Rosenhead and Winckelmans kernels.

## 6. Test numerical discretization

```bat
batch\34_run_C9_discretization_check.bat
```

This compares the continuum Rankine field with fixed-total-circulation discrete tube bundles at \(N=19,37,61\).

## Manual commands

```powershell
python src/sst_iso_gamma_area_clock.py campaign `
  --config configs/C9_iso_gamma_area_smoke.json `
  --output outputs/C9_iso_gamma_area_smoke
```

```powershell
python tools/analyze_iso_gamma_area.py `
  --input outputs/C9_iso_gamma_area_smoke `
  --output outputs/C9_iso_gamma_area_smoke/analysis
```
