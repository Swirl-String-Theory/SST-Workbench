# Changelog

## v0.3.1 — frozen-mode / numerical-certification correction

- Replaces one-shot FFT horizon extension with iterative multi-cycle certification and an explicit horizon-cap unresolved state.
- Freezes the certified horizon across action amplitudes for a carrier/resolution.
- Splits full material-marker and normal-projected centerline relative-equilibrium residuals; UA2b now gates on the normal residual.
- Adds adaptive arclength mesh-gauge control with pre-cleanup mesh diagnostics.
- Adds dynamic substep budgets derived from the requested horizon/CFL, with an absolute fail-closed cap.
- Adds dedicated broadband mode discovery, normal-bundle projection, RMS normalization, and frozen-mode reuse.
- Measures symmetric energy and frequency on the same frozen mode (`UA2d_matched_mode_energy_frequency`).
- Adds explicit complete-coverage gate `UA0b_complete_campaign_coverage`; numerical exceptions produce error rows rather than disappearing.
- Strengthens prerequisite semantics so unresolved recurrence/mode/mesh/energy/temporal stages cannot become downstream action claims.
- Keeps PTSA v1.0.0 unchanged and preserves strict SST-constant/SI blindness.
- Preserves versioned output convention with separate blind/revealed archives.

## v0.3.0 — PTSA / dynamic-carrier release

- Adds self-contained `SST_Parametric_Trefoil_Seed_Atlas_v1.0.0` (48 analytic candidates).
- Bundles exact `SST_Knot_Library_v0.2.5.zip` generator/provenance dependency (79 kB).
- Changes default dataset from KnotPlot final to PTSA.
- Adds dimensionless seed qualification before action testing.
- Rejects first-bin/window-limited spectral peaks and can extend horizon automatically.
- Adds explicit downstream `SKIP_PREREQUISITE` semantics.
- Implements global versioned output folder/archive convention with separate BLIND/REVEALED archives.
- Preserves strict SST-constant/SI blindness.

## v0.2.2 — Windows CMD/VS environment bootstrap hotfix

- Fixes the v0.2.1 Windows/Python 3.14 native-build failure occurring before C++ compilation in setuptools' `cmd /u /c vcvarsall.bat ... && set` bootstrap.
- Directly initializes `vcvarsall.bat`, verifies `cl.exe` and `link.exe`, and sets `DISTUTILS_USE_SDK=1` plus `MSSdk=1` before `build_ext`.
- Adds `run_01_build_native_clean.cmd` using `cmd.exe /d` to suppress registry Command Processor AutoRun hooks for the build child shell.
- Makes all major runners working-directory independent with `pushd "%~dp0"`.
- Invokes `.venv\Scripts\python.exe` directly instead of relying on activation for normal Python stages.
- No change to strict dimensionless blindness, scientific gates, thresholds, finite-core kernel, or reveal policy.

## v0.2.1 — strict SST-constant-blind anti-circularity correction

- Removes all SST canonical constants from the pre-reveal Universal Action campaign and scorer.
- Deletes the old `constants.py` and `action_constants.py` pre-reveal modules.
- Adds `reveal_constants.py`, imported only by reveal/provenance code.
- Replaces SI energy extraction with
  \[
  \hat E=\hat S/(8\pi).
  \]
- Replaces `delta_E_J`, `frequency_Hz`, `omega_rad_s` with
  `delta_E_hat`, `frequency_hat`, `omega_hat`.
- Blind normalization is fixed to \(L=1,\Gamma=1\).
- Adds a static `blind_guard` over source, config and blind payload schemas.
- Removes provenance execution from `run_all*.cmd`.
- Makes provenance explicitly reveal-only.
- Splits verdicts into dimensionless universal-action evidence and absolute Planck normalization.
- Adds optional reveal-only independent scale
  \[
  J_0=\rho\Gamma L^3.
  \]
- Legacy SST normalization is supplied only as a reveal-only contaminated negative control.
- Absolute Planck PASS is impossible without an explicitly independent normalization.
- Keeps RK4, \(\Delta t\propto\Delta s^2\), relative-equilibrium, frozen discovery/holdout, amplitude-continuity, temporal/spatial convergence, and blind identity quarantine from v0.2.0.

## v0.2.0

Introduced the integrated Wien–Planck field–matter and Universal Action workbench,
but the action path still used canonical SST values for SI dimensionalization before
blind scoring. v0.2.1 removed that remaining provenance vulnerability; v0.3.0 preserves the correction while changing the geometry population and qualification method.
