# SST VAM-5 × SST-17 + SST-33/35 v0.3.0

**Status: DEVELOPMENT / NOT PHYSICALLY CERTIFIED** (20 October 2026)

This is a versioned continuation of v0.2.0, not a modification of the historical papers or the registered PKLSA backend. It preserves the old 47-test baseline under `legacy_v020/`, and adds 55 new deterministic regressions for a **non-native** regularized filament Biot–Savart surrogate and corrected spectral-overlap/thermodynamic calculation modules. The 7-page manuscript includes equations, source audit, results, and a native engine contract.

## Quick start

From the root directory, install `pip install -r requirements.txt`, then:

```cmd
run_all.cmd
run_all.cmd PDF
```

Or Linux/macOS: `bash run_all.sh` (PDF is optional). The test order is legacy 47 checks, v0.3.0 55 checks, and plots/CSV generation. `run_all.cmd NATIVE` explicitly returns code 4 because the registered source-native PKLSA engine is not bundled. The PDF is precompiled.

## New v0.3.0 deliverables

- `SST_VAM5_SST17_PKLSA_Resonance_v0.3.0.pdf/.tex`: seven-page scientific document and editable LaTeX.
- `src/sst_v030.py`: regularized filament velocity / impulse / energy proxy / RK4, separate Gaussian-Lorentzian overlap and thermal-bar calculations.
- `tests/validate_v030.py`: 55 deterministic tests; `legacy_v020/validate_integrated.py`: the 47 inherited v0.2.0 tests without edits.
- `src/generate_figures.py`: reproducible plots and `results/ring_refinement.csv`.
- `results/v030_validation.json`, `results/validation_report.json`, `results/derived_scales.json`.
- `source_manifest.json`, `science_contract.json`, `gate_definitions.json`, `SHA256SUMS.txt`.
- `inputs/native_pklsa_manifest.schema.example.json`, `src/check_native_provenance.py`: optional input provenance prechecks, not native physics certification.

## Critical demarcations

1. Synthetic knots are **not** imported from E010/PKLSA; real native source and input path have not been supplied here. The filament simulation uses regularized midpoint segments, not the full 3D Euler pressure--Poisson solver. It cannot independently derive a photon, core stability, gravity, electrical charge, or Swirl-Clock proper time.
2. `Omega0=v_swirl/r_c` is a canonical kinematic scale only. The spectral module uses **synthetic** resonance peaks and does not measure Kelvin/Floquet modes from physical vortex trajectories.
3. SST-33 `T_swirl=Theta*epsilon` is a strain rescaling, not an independently derived equilibrium temperature. The Fourier-bar `delta kappa` values are conditional inputs; no source-native prediction of a 1% or 2% conductivity change is made.
4. The unnormalized Gaussian and Lorentzian spectra require factors `(sqrt(2 pi)*sigma)*(pi*Gamma)` multiplying the **unit-area** Voigt profile. This has been directly checked against quadrature. Both the amplitude definition and normalization must be specified in physical experiments.
5. The independent director field, effective stiffness and free Maxwell correspondence from v0.2.0 are preserved but not certified as native incompressible Euler dynamics.

## Native PKLSA follow-on integration (G5/G6)

Supply the existing canonical PKLSA source, source/seed provenance, native finite-core kernel, temporal integration and coordinate-unit conventions. Use external `src/check_native_provenance.py --xyz ... --manifest ...` for hash and metadata **preflight only**. Actual G5/G6 qualification requires an engine-native run at BASIC N=1200/2400, FULL N=4800/9600, separate spatial and temporal refinement, fixed final time, physical pressure/circulation/helicity, and independently identified modes. Do not call the local surrogate PKLSA or claim native GPU execution.

## Exclusions

No existing source file is edited in place. No hidden source access or Google Drive upload is asserted. No full Euler, PKLSA native, electromagnetic, gravitational, heat-capacity or quantum-spin claim is promoted by the passing regressions.
