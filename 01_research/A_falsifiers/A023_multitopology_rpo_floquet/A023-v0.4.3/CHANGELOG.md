# v0.4.3

- SYCL runtime/debug maintenance release; no scientific gate or threshold changes.
- Validates freshly built SYCL extensions in a child process so a native 0xC0000005 cannot kill the builder.
- Names the Biot-Savart SYCL kernel and uses per-kernel device-code splitting.
- Makes SYCL queue state function-local/lazy rather than a translation-unit global.
- Adds `run_sycl_diagnostics.cmd` with staged bind/device/float-kernel/double-capability probes.
- Sets `SYCL_CACHE_PERSISTENT=0` in SYCL launchers as a defensive workaround for a confirmed 2026 dynamic-SYCL-library cache crash.
- Adds an explicit native-FP64 capability check in diagnostics; FULL scientific GPU results must not silently downcast to FP32.

# Changelog

## v0.4.2 — Windows CPython/SYCL DLL-load fix

### Runtime fix only — no scientific gate/config changes
- Registers Intel oneAPI runtime directories with `os.add_dll_directory()` before importing the pybind11 `.pyd`.
- Keeps the returned DLL-directory handles alive for the full Python process lifetime, as required by CPython's Windows DLL loading model.
- Uses `SST_ONEAPI_DLL_DIR` / `ONEAPI_ROOT\compiler\latest\bin` and oneAPI directories inherited from `setvars.bat`.
- Preserves a successfully linked but failed-to-load SYCL `.pyd` instead of deleting it.
- Prints the exact extension-load exception, making missing `sycl9.dll`, Unified Runtime, or dependent-DLL failures directly diagnosable.
- SYCL `.cmd` launchers export `SST_ONEAPI_DLL_DIR` after `setvars.bat`.
- Scientific configurations, thresholds, P0--P8 semantics, 127-object inventory and source archives are byte-equivalent to v0.4.1.
- Embeds the exact immutable v0.4.1 release ZIP in `release_history/`.

## v0.4.1 — complete Fremlin + KnotPlot/RidgeRunner archive campaigns

### Archive coverage
- Expands archive enumeration from one Fremlin representative per directory to **every `.fseries` file**.
- Validated inventory: 78 Fremlin variants + 49 KnotPlot/RidgeRunner finals = **127/127 parseable geometries**.
- Writes `ARCHIVE_INVENTORY.csv/json` with source family, canonical topology label, variant and SHA-256.

### New run levels
- `configs/archive_extra_extended.json`: 240 points, Kelvin k=2..6, 3 epsilon levels, 220-step ringdown.
- `configs/archive_full.json`: 360 points, Kelvin k=2..8, 4 epsilon levels, 480-step ringdown, stricter convergence/linking drift and larger RPO/Floquet search.
- Adds `run_archive_extra_extended.cmd`, `run_archive_full.cmd`, strict oneAPI/SYCL variants, validation/inventory commands and resumable output command.
- Adds deterministic sharding with `run_archive_full_sharded.cmd` and merged reports.

### Scientific guardrails
- Keeps P0/P1/P2/P5 critical semantics unchanged.
- Adds an RPO compute precondition for archive-scale campaigns: clearly unstable spectra are not sent through expensive RPO/Floquet scans. P7/P8 become N/A when skipped; no stability evidence is inferred from skipping.
- Every Fremlin alternate representation is analyzed independently, enabling direct representation-sensitivity estimates.

### Reporting
- Adds `ARCHIVE_CONCLUSIONS.md` with class totals, gate-failure counts, growth rankings, variant spreads and RPO candidates.
- Adds full archive preregistration and 127/127 parser validation report.

### Reproducibility
- Embeds the exact immutable v0.4.0 release ZIP in `release_history/` in addition to the earlier releases.
- Retains both original source archives and their hashes.
- FULL and EXTRA_EXTENDED configs are immutable inside this release.

## v0.4.0 — Multi-Topology Knot/Link Comparative Panel

- Added blinded 17-input canonical panel spanning `0_1`, `3_1`, `4_1`, `5_1`, `5_2`, unlink controls, Hopf-like `link_2.2.1`, `link_6.3.1`, `link_6.3.3`, `T(2,3)` and `T(6,9)`.
- Added true multi-component parsing from RidgeRunner `vertices_per_component` metadata.
- Added `local + self_nonlocal + mutual = total` finite-core Biot--Savart decomposition.
- Added topology-agnostic breathing/torsion-sensitive/Kelvin Frenet-Fourier reduced basis.
- Added generic reduced Jacobian, epsilon convergence, family-coupling ablations and short nonlinear ringdown.
- Added high-resolution pairwise Gauss linking matrices and in-run linking-conservation gate for links.
- Added tube-thickness/core-radius self-contact gate; removed arbitrary chord-distance self-contact criterion for the multi-topology panel.
- Added excursion-before-return RPO scan and conditional multi-component Floquet return-map implementation.
- Added `GATE_CONCLUSIONS.md` and post-unblind `COMPARATIVE_CONCLUSIONS.md`.
- Added exact source archives and canonical selected inputs under `repro_inputs/`.
- Added `run_archive_survey.cmd` to screen all bundled KnotPlot/RidgeRunner final geometries and primary Fremlin Fourier-series files.
- Added safe deterministic resume: an interrupted panel resumes only if the preregistered config is byte-equivalent as parsed JSON.
- Retained v0.1.0, v0.1.1, v0.2.0 and v0.3.0 release ZIPs.
- v0.3.0 trefoil-specific lobe gates remain reproducible and are explicitly not replaced by the generic v0.4 basis.

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