# SST Dimensionless Dynamic Predictions v0.3.0

## Axial vortex-bundle research package

This release tests a trefoil embedded in a finite-radius bundle of vortex tubes that run from \(z=-\infty\) to \(z=+\infty\). The bundle radius is normally derived from the free central aperture of the knot:

\[
R_{\rm bundle}=\eta_h R_{\rm hole}^{\rm free}.
\]

The package deliberately separates two interpretations:

\[
\boxed{
\begin{array}{ll}
\text{physical tubes:}&\Gamma_{\rm tube}\ \text{fixed},\quad \Gamma_{\rm hole}=N\Gamma_{\rm tube},\\[1mm]
\text{numerical discretization:}&\Gamma_{\rm hole}\ \text{fixed},\quad \Gamma_{\rm tube}=\Gamma_{\rm hole}/N.
\end{array}}
\]

These are not equivalent experiments.

## Current scientific verdict

The included smoke tests show:

- the physical-tube flux scaling is implemented correctly;
- the fixed-total discrete representation converges to the continuum Rankine bundle;
- circulation produces a consistent phase/clock-rate diagnostic;
- the tested frozen hole-matched bundles do **not** stabilize the static Gilbert trefoil;
- full three-dimensional bending and mutual backreaction of the background tubes remains open.

At \(N=61\), the fixed-total discretization differs from the continuum field by approximately

\[
1.76\times10^{-4}
\]

in RMS background velocity and by approximately

\[
5.63\times10^{-4}
\]

in the intrinsic residual, averaged over both circulation signs.

The best exploratory continuum case reduced the isolated trefoil residual by only about \(0.60\%\), leaving

\[
\epsilon_{\rm int}\simeq0.2192\gg0.05.
\]

See `VALIDATION_AXIAL_BUNDLE.md`.

## B0–B8 ladder

| Gate | Test |
|---|---|
| B0 | isolated knot control |
| B1 | large-radius uniform-vorticity control |
| B2 | hole-matched continuum Rankine bundle |
| B3 | bundle-radius sweep |
| B4 | co-/counter-rotating chirality sweep |
| B5 | ring, trefoil, mirror-trefoil and figure-eight |
| B6A | physical tubes with fixed circulation per tube |
| B6B | numerical discretization with fixed total circulation |
| B6C | full 3-D tube backreaction — open |
| B7 | convergence to continuum Rankine bundle |
| B8 | circulation phase as clock-carrier diagnostic |

Full definitions are in `docs/07_axial_vortex_bundle_test_ladder.md`.

## Windows quick start

Unzip the package and run:

```bat
batch\01_setup_venv.bat
batch\20_axial_bundle_selftest.bat
batch\29_run_bundle_smoke_tests.bat
```

To run the two interpretations separately:

```bat
batch\21_test_physical_tubes.bat
batch\22_test_numerical_discretization.bat
batch\23_analyze_both_bundle_modes.bat
```

To run the complete test ladder:

```bat
batch\28_run_full_B0_B8_ladder.bat
```

B7 is the largest static convergence campaign.

## Python CLI

```bash
python src/sst_axial_vortex_bundle.py selftest
```

```bash
python src/sst_axial_vortex_bundle.py campaign --config configs/B6_physical_tubes.json --output outputs/bundle_physical_tubes
```

```bash
python src/sst_axial_vortex_bundle.py campaign --config configs/B6_numerical_discretization.json --output outputs/bundle_numerical_discretization
```

Then compare the modes:

```bash
python tools/analyze_bundle_modes.py --input outputs --output outputs/bundle_mode_analysis
```

## Primary output fields

Each row records:

- `central_hole_radius`;
- `free_hole_radius`;
- `bundle_radius`;
- `tube_count`;
- `circulation_per_tube`;
- `total_circulation`;
- `mean_vorticity`;
- `clock_omega`, `clock_period`, `clock_phase`, `clock_cycles`;
- `intrinsic_residual`;
- `residual_reduction_fraction`;
- `background_velocity_rms`;
- geometry and epistemic gates.

## Model boundary

The background tubes in v0.3.0 are:

- infinite and straight;
- parallel to the selected axis;
- frozen in position;
- finite-core regularized;
- externally imposed.

This package does not yet implement a fully coupled state

\[
\{X_K(s,t),X_1(z,t),\ldots,X_N(z,t)\}
\]

with tube bending, mutual induction, Kelvin modes or reconnection. Therefore a failure of the frozen-bundle tests does not falsify the stronger backreacting-bundle hypothesis.

## Epistemic status

\[
\boxed{[\mathrm{RESEARCH\ TRACK}]}
\]

The circulation phase is a clock-carrier diagnostic, not a derivation of proper time. No particle identification or dimensional SST constant is predicted by this package.