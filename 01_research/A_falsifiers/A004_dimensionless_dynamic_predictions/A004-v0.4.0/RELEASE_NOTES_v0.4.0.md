# Release notes v0.4.0

## Added

- C9 iso-\(\Gamma/A\) dynamic-clock falsification campaign.
- Independent trefoil phase measurement using the complex \(m=3\) geometric multipole.
- Matched isolated-run subtraction for self-induced rotation.
- Primary initial phase-rate \(T_{\rm dyn}\) estimator with uncertainty and linearity gates.
- Secondary strict multi-cycle period gate.
- FFT/autocorrelation consensus diagnostics for intrinsic shape observables.
- Continuum and fixed-total-flux discrete representations.
- Per-run falsifier
  \[
  \mathcal Q_\Gamma=2\Delta\Omega_{\rm dyn}/(\Gamma/A).
  \]
- Iso-family spread gate.
- Positive solid-body extractor control.
- Windows batches 30–34.
- New analyzer `tools/analyze_iso_gamma_area.py`.

## Validation status

- 18/18 unit tests pass.
- Synthetic phase and scalar-period controls pass.
- Solid-body positive control returns \(\mathcal Q_\Gamma\) within 0.7% of unity.
- Hole-contained continuum smoke campaign returns certified \(\mathcal Q_\Gamma\) values between 0.021 and 0.069 and therefore falsifies the sufficiency of bundle-average \(\Gamma/A\) for the trefoil phase rate within the frozen model.

## Model boundary

This remains a frozen straight-bundle harness. Tube bending, mutual induction, dynamic area selection and a proper-time identification are not implemented.
