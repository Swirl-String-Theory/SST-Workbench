# SST Finite-Core Axial–Toroidal Eigenmode + Self-Generated Phase-Delay Blind Falsifier v0.1.2

v0.1.2 is the **Swirl-Clock phase-integrity upgrade**.  It keeps the finite-core Chebyshev Euler eigenproblem and symmetric closure null from v0.1.1, but fixes the main weakness exposed by the v0.1.1 outputs: packet **delay** was reproducible while absolute **phase-at-return** was often under-resolved.

The hard rule remains:

\[
\boxed{\text{no feedback delay and no target phase are supplied to the dynamics.}}
\]

## What changed

- continuous sub-sample return-peak refinement;
- adaptive local phase resolution with default \(|\omega|\Delta t\le0.05\) rad;
- measured phase-uncertainty gate, including accumulated dispersion-fit uncertainty;
- real cycle count \(|\Im\lambda|\tau_{ret}/2\pi\);
- co-moving `omega_intrinsic` in addition to lab-frame `Im(lambda)`;
- eigenvector-overlap continuation across axial-flow scans;
- preregistered `FAST_SWIRL_LOCKED` versus `SLOW_MODE` classification;
- bounded growth response for phase regressions;
- the old `2.72 rad` target is retired because the observable changed;
- new `m=1` phase **discovery**, not confirmation;
- separate `m=2` phase diagnostic and phase-resolution stress test.

See `CHANGELOG.md` for the reason behind every design choice.

## Swirl-Clock core set

\[
\boxed{
\{\Re\lambda,\Im\lambda,\omega_{intrinsic},\Omega_{swirl},v_g,
\tau_{loop},\tau_{return},\phi_{loop},\delta\phi\}.
}
\]

The physics question is now sharper:

\[
\text{same continued eigenbranch}
\rightarrow
\text{measured return}
\rightarrow
\text{numerically certified phase}
\stackrel{?}{\longrightarrow}
\Re\lambda\downarrow.
\]

## Recommended order

Install/build/test/basic:

```cmd
run_all.cmd
```

Primary v0.1.2 clock campaign:

```cmd
run_all_swirl_clock_phase_discovery.cmd
```

Then:

```cmd
run_all_swirl_clock_branch_map.cmd
run_all_phase_resolution_stress.cmd
run_all_swirl_clock_m2_diagnostic.cmd
```

Existing broad campaigns remain available:

```cmd
run_all_extended.cmd
run_all_profile_robustness.cmd
run_all_core_radius.cmd
run_all_chirality_sign.cmd
run_all_radial_convergence.cmd
```

Everything:

```cmd
run_all_full.cmd
```

## Discovery output

`outputs/swirl_clock_phase_discovery/reveal/PHASE_DISCOVERY.json` may contain a newly estimated `phase_min_rad`.  That value is explicitly marked discovery-only.  It must not be treated as confirmed until a later version freezes it before independent data are run.

## Interpretation

A positive delay gate establishes propagation timing, not feedback stabilization.  A positive phase association is still only a finite-core linear mechanism gate.  A full curved-core Euler/Floquet/nonlinear orbital-stability calculation remains downstream.
