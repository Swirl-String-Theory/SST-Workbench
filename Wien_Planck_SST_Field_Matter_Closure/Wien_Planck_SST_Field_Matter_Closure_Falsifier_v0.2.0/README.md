# Wien–Planck SST Field–Matter Closure Falsifier v0.2.0

v0.2.0 turns the v0.1 spreadsheet-style action comparison into a **raw-geometry → dynamics → frozen intrinsic mode → energy/action → blind reveal** pipeline.

## Central falsification question

\[
\boxed{\text{Does free SST-like vortex dynamics generate an amplitude-independent, carrier-independent action spacing?}}
\]

A discrete mode spectrum by itself is explicitly insufficient. The strongest negative control is the ordinary classical expectation \(E\propto A^2\), which implies \(\Delta E/f\propto A^2\).

## One-click Windows chain

```bat
run_all.cmd
```

Default dataset:

```text
..\..\KnotPlot\knots\final
```

Or:

```bat
run_all.cmd "C:\workspace\projects\SST-Workbench\KnotPlot\knots\final"
```

The chain performs:

```text
venv/setup
 -> native C++17/pybind11 build (required for scientific run)
 -> native/Python self-tests
 -> runtime source/dependency code seal
 -> provenance audit
 -> dataset inventory + source hashes
 -> RK4 finite-core line-filament campaigns
 -> relative-equilibrium diagnostic
 -> matched +/- broadband probes
 -> discovery-only POD / frozen holdout mode
 -> energy extraction using rho_f (not rho_core)
 -> blind prepare + private commitment
 -> blind action/discreteness/convergence analysis
 -> BLIND report
```

It deliberately **does not auto-reveal**.

After saving the blind report:

```bat
run_40_reveal.cmd outputs\basic_YYYYMMDD_HHMMSS
```

## Presets

```bat
run_all.cmd [dataset]              rem quick/basic
run_all_extended.cmd [dataset]     rem N=64,96,128
run_all_highres.cmd [dataset]      rem N=128,256,512
```

## Why this is stronger than v0.1.0

- no externally supplied `delta_E_J` is needed for the native geometry campaign;
- \(\Delta E\) is extracted from a committed h-free line-energy ledger;
- the frequency comes from a discovery/holdout intrinsic-mode analysis;
- \(+\epsilon/-\epsilon\) arms isolate odd response;
- RK4 uses \(\Delta t\propto\Delta s^2\), fixed final time and scheduled reparameterization;
- a relative-equilibrium residual prevents a geometrically relaxed curve from silently being called dynamically stationary;
- the blind scorer includes a **classical continuous-action null**;
- relative-equilibrium and temporal-convergence gates are hard prerequisites;
- raw identities are quarantined outside the BLIND archive;
- target constants appear only in the final reveal;
- links remain multi-component.

## Scientific non-claims

The regularized line-filament backend is not full 3-D finite-core Euler DNS. The energy functional is a model diagnostic. A frozen spectrum is not Floquet. No true Floquet monodromy is claimed without a closed relative-periodic orbit. No entropy production is assumed for ideal Euler flow.

See `docs/THEORY_AND_GATES.md`, `docs/PRIOR_CONCLUSIONS_INTEGRATED.md`, and `PROVENANCE_AUDIT.md`.

## Focus runners inherited from prior intrinsic-modal work

```bat
run_focus_6p3.cmd
run_focus_link_9p2p20.cmd
run_focus_link_4p2p1_control.cmd
run_focus_trefoil_3p1.cmd
```

See `docs/SCIENTIFIC_STATUS.md` for the exact implemented/non-implemented boundary.
