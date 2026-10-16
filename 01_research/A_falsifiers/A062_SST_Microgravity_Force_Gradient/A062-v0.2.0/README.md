# A062-v0.2.0 — Genuine E011 trefoil Kelvin-impulse force-gradient candidate

**Scientific status: exploratory, not established SST gravity.** Replaces the v0.1.0 Gaussian surrogate with **actual raw original E011** static-ready 3_1 primary provider anchors (Gilbert Fourier original + KnotPlot Geomview VECT). Raw SHA-256 is checked against E011 v0.3.0 `topologies/3_1/STATIC_READY_SEEDSET.json`. Source files are bundled. These are two independent **geometry providers**, not two gravity experiments.

## Scope

- Euler/incompressible/inviscid 3-D; Rosenhead-regularized Biot-Savart velocity for finite-radius prescribed vortex **filaments**.
- Kelvin impulse change `dI_B/dt|A→B = rho_f Γ_B ∮ v_A × dX_B`, separating the contribution of the external vortex (no Newton G is used).
- Two-way exchange action–reaction, axial separation exponent, orientation/chirality controls, finite difference force gradient, N=48/96/192/384 convergence, separate C++17 strict FP64 parity.
- Optional inexpensive 24³/36³ periodic Poisson diagnostic. **It does not resolve r_c** and therefore is NOT a physical isolated-space pressure or total stress force solution.
- `STATIC_READY ≠ DYNAMICS_READY`. No self-confinement, Euler time evolution, mass closure, or G derivation is claimed.

## Install / Workbench

Drop `A062-v0.2.0` under

`SST-Workbench/01_research/A_falsifiers/A062_sst_microgravity_force_gradient/`

Install Python 3.11+ and `pip install -r requirements.txt`. A C++17 compiler (`g++`, `clang++` or MSVC) is needed for native parity. No GPU is needed. Typical standalone CPU FULL run takes seconds on a desktop; the core 3-D pressure resolution needed for physics is deliberately not attempted.

```bat
run_science.cmd SELFTEST
run_science.cmd FREEZE
run_science.cmd BASIC
run_science.cmd FULL
run_science.cmd CERTIFY
```

`FREEZE` is create-once; after freezing any source change requires a new version. The standalone hash lock is independent of shared-framework certification.

For true framework v1.0.7 execution, the external frozen framework must exist at `06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.7` and be properly configured. Only then:

```bat
run_all.cmd FREEZE
run_all.cmd FULL
run_all.cmd CERTIFY
```

A `run_all.cmd` success must be confirmed locally; no v1.0.7 framework runtime is shipped inside A062.

## Physics and caveats

Vortex-filament Kelvin impulse is a legitimate hydrodynamical observable; treating its **subpopulation** rate as the complete force on a macroscopic material body is *not* a valid shortcut. 3-D finite-core dynamics, an isolated-space Euler-Poisson momentum balance and a particle mass definition require further independent study. A source that changes sign under relative orientation is not universal gravity.

Given E011 `reach` for each original carrier, we test the explicit scale scenario `L_physical=r_c/reach`. These reach/core notions are not demonstrably equal; no SST constant is derived. Signs of raw Gilbert and KnotPlot writhe differ, so we report the original chiral geometry without silent reflection.

## Inputs

`inputs/raw/Ideal.txt.gz` — Gilbert original (record `3:1:1`, SHA-256 `274a4ce111607a6295e280f3f8369c665e7de82ac33afcd4cb227eb61568d530`).

`inputs/raw/knot_3.1_trial_001k_rr_010k_coarse.final.vect` — KnotPlot original (SHA-256 `8fea8a15ff3047dbbfb4aba05090b9a6cadc10eeedf97c22350925c764bc540e`).

`inputs/e011/trefoil_STATIC_READY_SEEDSET.json` — E011 derived qualification metadata. Counts and provider IDs must not be construed as independent physical measurements.

## Outputs

`A062_SST_Microgravity_Force_Gradient_v0.2.0-outputs/` within the instance, a sibling `-outputs_BLIND.zip` (name indicates **unrevealed package**, not a genuinely blinded article-based confirmation), and a sibling `*_FALSIFIER_REPORT.pdf`.

Equations and source references: `report/FALSIFIER_REPORT.tex`.
