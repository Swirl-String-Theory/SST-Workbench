# Changelog

All releases are immutable research snapshots. New releases keep prior release ZIPs in `release_history/` and preserve their original configs/code.

## v0.3.0 — coupled torsion/breathing/Kelvin balance + guarded RPO/Floquet

### Scientific analysis
- Preserves the original critical overall rule `G0/G2/G3/G4/G6` without modification.
- Retains all v0.2 causal/contact diagnostics unchanged.
- Adds a separate expanded centerline basis containing:
  - legacy tilt and breathing modes;
  - three smooth lobe-windowed binormal **torsion-sensitive** modes;
  - normal/binormal Kelvin-like Fourier perturbations at configurable harmonics.
- Adds multiple-\(\epsilon\) expanded Jacobian convergence checking.
- Adds family participation for every expanded eigenvector.
- Adds reduced causal family ablations:
  - decouple breathing;
  - decouple torsion;
  - decouple Kelvin;
  - decouple tilt;
  - remove all inter-family couplings by block diagonalization.
- Defines growth penalties relative to the fully coupled spectrum, so a positive penalty has an unambiguous stabilizing interpretation.

### Relative-periodic-orbit search
- Selects a complex oscillatory eigenmode with simultaneous breathing/torsion/Kelvin participation.
- Phase-scans the real/imaginary eigenvector plane and performs full nonlinear finite-core Biot–Savart evolution.
- Adds Kabsch symmetry reduction and normal-shape recurrence.
- Adds a mandatory **excursion-before-return** criterion.
- Adds a return-ratio criterion so slow monotonic drift cannot be mislabeled as an RPO.
- Rejects candidates that encounter the configured near-core threshold.

### Phase locking
- Adds windowed dominant-frequency analysis for the strongest breathing, torsion and Kelvin projected coordinates.
- Adds circular phase-difference coherence across windows.

### Conditional Floquet analysis
- Floquet is not run/interpreted unless the RPO recurrence gate is satisfied.
- Builds a nonlinear finite-difference return-map monodromy matrix in a deterministic reduced subspace.
- Invalidates the result if the reference or any \(\pm\epsilon\) return trajectory reaches a near-core event.
- Reports all multipliers, a candidate neutral multiplier nearest unity, and spectral radius excluding that multiplier.

### New diagnostic gates
- `G12_TBK_mode_resolved`
- `G13_torsion_coupling_stabilizes`
- `G14_kelvin_coupling_stabilizes`
- `G15_breathing_coupling_stabilizes`
- `G16_TBK_collective_coupling_stabilizes`
- `G17_TBK_phase_lock`
- `G18_RPO_recurrence`
- `G19_Floquet_bounded`

### Reporting
Adds:
- `coupled_spectrum.csv`
- `family_coupling_ablation.csv`
- `phase_lock.csv`
- `rpo_phase_scan.csv`
- `floquet_multipliers.csv`
- expanded TBK/RPO/Floquet sections in `REPORT.md` and `GATE_CONCLUSIONS.md`.

The blind `*_arrays.npz` also retains expanded modes, expanded Jacobians, and a valid Floquet monodromy matrix when available.

### Reproducibility
- Adds the immutable v0.2.0 ZIP to `release_history/` while retaining v0.1.0 and v0.1.1 directly.
- Historical runners now recompute v0.1.0, v0.1.1, v0.2.0, then v0.3.0 from the same bundled inputs.
- Keeps all thresholds in versioned JSON configs and all scientific gate wording in the release.

## v0.2.0 — deeper causal decomposition

### Scientific analysis
- Preserves v0.1 critical decision rule: `G0/G2/G3/G4/G6` remain the overall PASS/FAIL critical set.
- Adds exact **biorthogonal left/right eigenmode attribution** for the reduced Jacobian:
  \[
  \lambda_k=\lambda_k^{\rm local}+\lambda_k^{\rm same}+\lambda_k^{\rm cross}+\lambda_k^{\rm transition}.
  \]
  This separates “cross-lobe locally repels” from “cross-lobe stabilizes the unstable eigenmode”.
- Adds component-ablation spectra: full, without-local, without-same-lobe, without-cross-lobe, without-transition, plus component-only spectra.
- Adds `C_3` reduced-sector diagnostics for `m=0` versus the real two-dimensional `E` sector and tilt/breathing participation.
- Adds top-K distinct close cross-lobe contacts with distance, tangent dot product, angle, antiparallelness, and per-component separation rate.
- Adds lobe-centroid pair separation rates computed from source-lobe segment fields without creating artificial closure segments.
- Adds curvature-signature matching for orientation-scrambled controls.
- Adds short nonlinear **full vs without-cross-lobe counterfactual evolution** initialized along the dominant reduced eigenmode.

### New diagnostic gates
- `G7_matched_orientation_specificity`
- `G8_cross_repulsion_coherent`
- `G9_dominant_mode_cross_stabilizes`
- `G10_C3_sector_localized`
- `G11_counterfactual_causal_consistency`

These gates deepen interpretation but do not retroactively change the v0.1 critical decision rule.

### Reporting
- Adds `GATE_CONCLUSIONS.md`: question, role, PASS/FAIL, conclusion, evidence, and threshold for every gate and every dataset.
- Adds `gate_conclusions.json` for machine-readable gate reasoning.
- Adds `modal_attribution.csv`, `contact_pairs.csv`, and `component_ablation.csv`.
- Adds plots for dominant-mode component attribution, orientation versus cross-lobe separation, and full/no-cross counterfactual evolution.

### Reproducibility / release history
- Bundles exact reproducibility inputs in `repro_inputs/`.
- Bundles immutable v0.1.0 and v0.1.1 release ZIPs in `release_history/`.
- Adds `run_reproduce_history_basic.cmd` and `run_reproduce_history_extended.cmd`.
- Adds `docs/REPRODUCIBILITY.md`, input/archive SHA-256 index, and historical reference conclusions.

## v0.1.1 — Windows build/release fixes
- Replaced broken nested `FOR /F` timestamp command with `tools/timestamp.py`.
- Generic install explicitly builds OpenMP and avoids accidental uninitialized oneAPI/SYCL linkage.
- `run_gpu_sycl.cmd` initializes oneAPI and requires a genuine SYCL build/load.
- Added compact `run_summarize.cmd`.
- Scientific gates and algorithms remained equivalent to corrected v0.1.0.

## v0.1.0 — initial blind trefoil lobe-orientation falsifier
- Blind Fremlin/KnotPlot source assignment.
- Uniform arclength resampling and finite-core calibration.
- Six reduced tilt/breathing modes.
- Local/same-lobe/cross-lobe/transition finite-core Biot–Savart decomposition.
- Reduced Jacobian, scrambled controls, finite-amplitude ringdown, circle null.
- No reconnection, hard-core bounce, cut/splice, or penalty-force operator.
