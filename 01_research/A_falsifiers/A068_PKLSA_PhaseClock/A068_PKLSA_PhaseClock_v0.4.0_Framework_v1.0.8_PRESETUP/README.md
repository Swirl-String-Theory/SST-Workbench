# A068 v0.4.0 - Lagrangian Material Tubes, Full-field RPO, Euler Floquet

## One-click run on the Windows SST-Workbench

Extract the complete ZIP, then run `SETUP_A068.cmd` with Python 3, NumPy,
SciPy and pytest available. It uses the **official** installed SST Falsifier
Framework v1.0.8 generator. It does **not** install/edit the framework or
overwrite v0.3.0; it creates A068-v0.4.0. The setup validates SHA-256 manifest,
science/gate/source/LaTeX contract, 26 numerical regressions, framework locator,
private keys, and performs official `run_all.cmd FREEZE` on Windows.

Commands from newly created instance:

```
run_all.cmd BASIC
run_all.cmd FULL
run_all.cmd CERTIFY
run_all.cmd REVEAL_IF_ALLOWED
```

## Science changes (v0.3.0 -> v0.4.0)

* **Actual 3D material transport**: closed triangulated toroidal tracer mesh
  around 47-point native KnotPlot trefoil; mesh positions and unforced Euler
  velocity share identical RK4 stages. Material volume drift, area, vorticity
  tangency and closed-surface flux separately calculated. **Material surface
  does not automatically qualify as a vortex tube.**
* **Full-field relative periodicity candidate search**: minimize mismatch
  of all 3*N^3 Euler velocity components over periodic translations and 24
  proper cube rotations, including sub-grid shift refinement. Frozen t0=0
  candidate scan only, **not** converged Newton-Krylov RPO shooting.
* **Independent Euler tangent/Floquet operator**: exact derivative from
  unchanged original A064 Euler equations, finite-difference checked; the
  analytical two-mode manufactured oracle is a regression test. Matrix-free
  relative monodromy + fixed-seed Ritz *candidate* only when material tube
  and RPO screens pass. No measured scalar phase is used as operator input.
* Physical gates G3 onward remain **UNRESOLVED / NOT_RUN_PREREQUISITE** without
  actual material-vortex tangency, shooting, resolved Floquet multipliers,
  convergence, independent providers, and SI calibration. No blind reveal
  bypass. Historical v0.3.0 run data stay development evidence.

## Executed development results and boundaries

Local v0.4.0 26/26 pytest PASS. A genuine BASIC 16^3 Euler run with 151
snapshots yielded full-velocity-field best relative RPO candidate residual
0.07778586994 (required <0.025), initial mean |omega.n|/|omega|
0.0821394429 (required <0.05), and maximum numerical material-volume drift
0.06152645 (required <0.05). Therefore no qualified vortex tube, RPO,
or physical clock. Exact Euler tangent finite-difference error ~2.08e-11;
independent manufactured Floquet oracle PASS. The FULL five-trajectory
campaign was not completed in the packaging environment and must be run on
workstation before making further convergence claims.

Sources are one geometry/solver provenance family; refinements do not count
as independent physical providers. Box L=2*pi, a=0.4, Gamma=1 are arbitrary
model units, not SST canonical scales. Historical sources and A064 solver are
byte-identical to v0.3.0; frozen v0.3.0 is unchanged.
