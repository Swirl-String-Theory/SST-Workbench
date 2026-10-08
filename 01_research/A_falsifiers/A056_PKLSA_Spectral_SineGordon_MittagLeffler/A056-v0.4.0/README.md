# A056-v0.4.0 - Circular/Fourier PKLSA Spectral Sine-Gordon Mittag-Leffler Falsifier

**Framework:** SST Falsifier Framework **v1.0.6 CANONICAL_FROZEN**  
**Status at release assembly:** implementation/preregistration validation; no official v0.4.0 m=4 physics result claimed.

A056-v0.4.0 is a new scientific release because the blocking G2 spectral test changes. It preserves the E010/PKLSA -> finite-core/Biot-Savart or Euler -> paired Kelvin phase/ringdown -> SG/ML pipeline from v0.3.0, but replaces the raw-phase early/late POD overlap as a blocking criterion.

The motivation is the frozen v0.3.0 development result: all four real filament cases were strongly low-dimensional (top-three raw POD energy > 0.99996 and machine-precision orthogonality), yet their raw early/late POD overlaps were only about 0.63-0.73. v0.4.0 does **not** lower the old 0.85 threshold. Instead it treats the old result as development-only and preregisters a phase-topology-aware test before running fresh v0.4.0 data.

## New blocking G2

For the circular embedding

\[
z(s,t)=e^{i\varphi(s,t)},\qquad \widetilde z=z-\langle z\rangle_s,
\]

v0.4.0 requires:

\[
\eta_3^{\rm circ}\ge0.95,
\qquad
\epsilon_{\rm orth}^{\rm circ}\le10^{-10},
\qquad
\mathcal O_F\ge0.90,
\]

where \(\eta_3^{\rm circ}\) is the top-three circular-POD energy fraction and \(\mathcal O_F\) is the Bhattacharyya overlap between discovery- and confirmation-window normalized non-zero spatial Fourier-power spectra of \(e^{i\varphi}\).

The historical raw-phase split-POD overlap is still written to diagnostics, but it cannot block or rescue G2. The circular-POD early/late subspace overlap is also diagnostic only. The Mittag-Leffler \(\alpha=1\) exponential identity remains a required analytic check.

## Fresh confirmatory dynamic input

The observed v0.3.0 filament campaign used the Kelvin \(m=3\) perturbation and is explicitly a development set. Official v0.4.0 E010 campaigns use the frozen fresh perturbation:

```text
perturbation_id = kelvin_m4_eps003_v040_preregistered
mode m          = 4
epsilon         = 0.03
```

This is the available out-of-sample axis because E010-v0.3.1 exposes only two strict new-upstream-provider trefoil representatives and both were already used in the v0.3.0 provider design. A separate Euler lane remains an additional solver/mechanism check.

## Provider lanes

`run_e010_filament.cmd` runs the regularized finite-core Biot-Savart filament campaign. `run_e010_euler_smoke.cmd` runs a short 3-D incompressible pseudo-spectral Euler campaign. `run_e010_euler_convergence.cmd` runs the preregistered multi-resolution Euler ladder. All generated E010 dynamics are `evidence_class=simulation`; they can establish a replicated simulation conclusion but cannot close physical G7.

## Commands

```bat
run_all.cmd
run_e010_filament.cmd C:\workspace\projects\SST-Workbench
run_e010_euler_smoke.cmd C:\workspace\projects\SST-Workbench
run_e010_euler_convergence.cmd C:\workspace\projects\SST-Workbench
```

A read-only development reanalysis of an existing sibling v0.3.0 runtime is available as:

```bat
run_diagnose_v030_development.cmd
```

Its output is never consumed by the v0.4.0 gate chain.

## Gate semantics

`G0 -> G1 -> G2 -> G3 -> G4 -> G5 -> G7 -> G8`, with optional non-blocking `G6` branching from G5 and commitment-verified reveal at G9. A G2 failure means the preregistered spectral representation failed admission; it is **not** a Sine-Gordon or Mittag-Leffler falsification because G3 was not run.

## Framework pin

The instance uses the v1.0.6 `framework_bootstrap.py`, `run_python.cmd`, output integrity checks and `REVEAL_IF_ALLOWED` orchestration. The canonical framework itself is not modified by A056.
