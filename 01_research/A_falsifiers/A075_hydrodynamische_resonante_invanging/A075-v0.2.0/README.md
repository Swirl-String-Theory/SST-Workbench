# A075-v0.2.0 — 3D Euler finite-core localization and knot-screening

**Status: DEVELOPMENT_ONLY; physical question UNRESOLVED.** No claim of lasting capture or photon identification. Source extends A075-v0.1.0 without changing its frozen protocol. The entire v0.2.0 protocol is new and has **not been frozen using the authentic Framework v1.0.10 in this environment**. The framework itself is NOT bundled.

## Central falsifier question
Can a freely evolving, fully coupled vortical receiver retain positive additional local energy **after** the incoming excitation has independently departed, for many independent receiver cycles, while local energy flux, core deformation and convergence all close?

## Science engine
- Fully 3D *periodic Fourier-Galerkin* incompressible Euler reference solver; `dt` fourth-order Runge–Kutta, 2/3 de-aliasing, Fourier-Leray projection, pressure-Poisson (via Lamb-vector projection), and zero viscosity.
- Three smooth finite-width vorticity objects: two receivers and a separate incoming `0_1`; never prescribes a circular configuration during evolution. Finite-core *initial condition* uses Gaussian Fourier smoothing of a solenoidal deposited filament current. It is not an independently established superfluid/physical core constitutive model.
- Analytic `0_1` unknot and `3_1` T(2,3) trefoil; original `5_2`/`6_1` files are **required** for their cases (see `inputs/README.md`). No artificial substitution.
- Matches no-donor and donor run in the **same translating fixed-shape smooth control window** (the center is determined from the no-donor run). Smooth window flux balance must converge with resolution/width. This is not a deforming material volume, though the moving-frame formula is exact for an arbitrarily prescribed boundary velocity in the continuum.
- Measures total kinetic-energy drift, `div(u)`, maximum Courant number, approximate moving-window pressure-energy flux and separately compares spatial and temporal refinements at the identical final absolute time.
- Does not infer source exit from apparent z-centerline displacement; must verify material-core departure with separate tracers/vorticity diagnosis before G3 can pass.
- Receiver oscillation probe is not qualified as clock unless multiple resolved peaks exist with stable period under mesh/time/geometry changes; no cycles are invented.
- Default `PREVIEW` and `BASIC` are intentionally *underresolved* initial fields for software smoke screening. Do not interpret their positive late window energy as retained energy.

## Execution
On Windows with the real shared Framework at `C:\\workspace\\projects\\SST-Workbench\\06_templates\\SST_Falsifier_Framework\\SST_Falsifier_Framework_v1.0.10`:

```
python -m pip install -r requirements.txt
python -m pytest -q tests
python tools/prepare_private.py  REM create fresh local-only reveal nonce and public commitments
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd FULL
```

The absolute environment override `SST_FALSIFIER_FRAMEWORK_ROOT` is honored and validated by `framework_bootstrap.py` and the `__version__=1.0.10` check. Do NOT run REVEAL; physics gate G8 is unresolved. Framework creates unique run IDs and output archives; release artifacts from a standalone PREVIEW are **not** the same as authenticated Framework runs.

Offline science-only smoke (NOT framework FREEZE):

```
python run_preview.py --profile PREVIEW
```

The default results go to `./A075_Hydrodynamische_Resonante_Invanging_v0.2.0-outputs/science/`. Source and bundled preview outputs have separate checksums. Never delete older v0.1.0 output roots. On the local Workbench, `run_all.cmd FULL` is substantially more expensive (three field trajectories per knot and grid level; 96-cubed upper mesh).

## Frozen prerequisites and acceptance gates
- G0: authentic framework v1.0.10 FREEZE, with **new private key/commitments**; prior v0.1 private metadata is not reusable.
- G1: byte-verified A021/A032 methodology sources; geometry hashes and independent topological identity checks for 5_2/6_1.
- G2: solver no-loss plus distinct fixed-physical-time spatial and temporal diagnostics with resolved core width (>= 3 grid points per Gaussian width on the coarse grid, *necessary not sufficient*).
- G3: predeclared source exit, no-return, minimum late excess significantly greater than all error budgets, >=100 independently resolved local receiver cycles, closed pressure and advective flux.
- G4: preregistered held-out configurations before inspecting positive capture data.
- G5/G6: native C++ and device parity remain not run.
- G7: independent geometry source and knot family sensitivity.
- G8: full periodic-box/core-profile/control-volume convergence and verified vorticity/topology fidelity. A Fourier-Galerkin field *implementation* does not mean fully physically resolved Euler.
- G9: private reveal prohibited until qualifying G8 and locked framework permissions.

## Scientific non-promotion
An initial donor field overlaps the receiver, and the initial total energy is not the isolated donor self-energy (kinetic cross term). A positive short-time window-energy difference is **not** absorbed donor energy. The smooth window tracks a passive marker, not an automatically material surface. Periodic replicas can create delayed interactions, hence box-size independence is an additional gate. A Gaussian starting vorticity width is not synonymous with a dynamically proven finite-core equilibrium. The user-provided analytic trefoil is an initializer, not an asserted stable eigenmode. Do not promote intrinsic clock, Floquet, photon absorption or atomic ontology.
