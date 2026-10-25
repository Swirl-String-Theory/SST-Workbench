# A003 TwistKnot Flow Lab P4 — tracer motion, streamline coexistence and numerical-step observability

## Observed symptom

In P3 the dedicated route loads the shared renderer and computes streamlines but the user sees neither the knot nor passive tracer particles moving.

## Verified source-level causes

1. The original `stepTracers(dtSim)` explicitly returned when `P.showStreamlines` was enabled. `trPts.visible` also suppressed the particle layer in streamline mode. Hence streamline mode did not merely *hide* the tracers; it also prevented their integration.
2. Streamlines are repeatedly reconstructed as *instantaneous tangent curves*, even when no physical step has been accepted. Seeing lines is not evidence that `tPhys` increased.
3. The default SST parameterization has circulation `nQ * 9.68361920e-9 m²/s` (normally `nQ=10`) in geometry of order `R0=0.07 m`. On a seconds-scale run, physically induced movement is extremely small in a centimetre-scale viewport. Accelerating the **requested playback rate** does not guarantee higher realised throughput if finite timestep and CPU gates limit accepted steps.
4. The P3 page labelled the engine `actief` merely because `bPause` was not paused. A hard safety stop did not change that label.

## P4 implementation

- Dedicated route `/twist-flow/` opts in with `window.__vlTwistFlowOverlayParticles=true` before it loads the shared runtime. Only on this route the existing `stepTracers` integrates and renders particles *at the same time* as instant streamlines.
- Original root VortexLab keeps its prior semantics; no change to the kernel, Circulation law, RK4 numerical integration, CFL limits, topology guard or physically unresolved cores.
- The shared runtime exposes a read-only snapshot `window.__vlTwistFlowDiagnostics()`: paused/halted flag, raw simulation time, accepted step count, pending and candidate timesteps, chosen circulation and playback multiplier, native vertices and drawing toggles.
- Dedicated UI reports *actual accepted steps*, distinguish paused, hard-stopped and potentially stalled cases. The snapshot does not advance the engine and does not manufacture motion.
- New flow mode **Tracers + lijnen**; existing Tracers and Alleen knoop options remain.
- Default particles reduced from 1,200 to 250, and streamlines from 16 to 8, to reduce CPU overhead while using native 1,024-point filament geometry.
- Native SST mode remains the initial/default physical interpretation. A dedicated **Bewegingsdemo starten** button opts into the **existing** demo-circulation mode, `Γ=2×10^-4 m²/s`, LIA (local induction approximation) and 100× requested playback. The button does not represent an SST prediction or calibrated physical constant. It switches the existing solver model; it is not a UI-only fake animation. Original full Biot–Savart remains an option.
- Core length and P2 `a_sim=1e-18 m` numerical qualification are retained without silent upscaling.

## Scientific status / limitations

**Software regression PASS, physical qualification remains DEVELOPMENT.** A P4 demo run changes Gamma and the model (LIA), therefore must not be compared numerically with the SST/BS baseline without acknowledging both changes. Even the demo can remain slow at native N=1024 due CPU limits, or halt on real topology/contact/CFL conditions. No guarantee of perceptible macroscopic motion at the physical SST speed is made.

This patch does *not* implement a new Euler pressure solver, full cylinder wall boundary conditions, new finite-core theory, GPU acceleration or a proof of twistknot stability.

No real browser end-to-end test was possible: Chromium navigation to loopback is blocked by administrator in this environment. Unit, regression, package, source-integrity and local HTTP route checks were executed.

## Install and run

Extract FULL to a clean directory, `cd A003_vortexlab`, run `npm run check`, then `npm start` and open `http://127.0.0.1:4173/twist-flow/`.

For OVERLAY, close the simulator, back up the existing P3 tree and extract OVERLAY at the same root, preserving relative directories. Run `npm run check`.

At first launch choose *Start* and inspect `Geaccepteerde stappen`. For visibly moving demo click **Bewegingsdemo starten**. A hard stop is reported with its exact engine reason; Reset clears the stop but does not validate a bad seed.
