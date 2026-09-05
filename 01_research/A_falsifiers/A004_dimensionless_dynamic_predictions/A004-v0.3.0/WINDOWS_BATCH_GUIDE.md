# Windows batch guide — v0.3.0

## 1. Install

Run once:

```bat
batch\01_setup_venv.bat
```

## 2. Verify the implementation

```bat
batch\20_axial_bundle_selftest.bat
```

Expected result: all flux and clock checks pass.

## 3. Fast paired test

```bat
batch\29_run_bundle_smoke_tests.bat
```

This runs a compact physical-tube ladder and a compact fixed-total discretization ladder, then generates:

```text
outputs\bundle_smoke\analysis\BUNDLE_MODE_ANALYSIS.md
outputs\bundle_smoke\analysis\bundle_mode_analysis.json
outputs\bundle_smoke\analysis\numerical_discretization_convergence.csv
```

## 4. Physical tubes

```bat
batch\21_test_physical_tubes.bat
```

Meaning:

\[
\Gamma_{\rm tube}=\text{constant},
\qquad
\Gamma_{\rm hole}=N\Gamma_{\rm tube}.
\]

Do not interpret increasing \(N\) as numerical convergence.

## 5. Numerical discretization

```bat
batch\22_test_numerical_discretization.bat
```

Meaning:

\[
\Gamma_{\rm hole}=\text{constant},
\qquad
\Gamma_{\rm tube}=\Gamma_{\rm hole}/N.
\]

This must converge toward the continuum Rankine reference.

## 6. Compare both modes

```bat
batch\23_analyze_both_bundle_modes.bat
```

## 7. Continuum ladder B0–B5

```bat
batch\24_run_B0_B5_continuum_ladder.bat
```

## 8. Both B6 interpretations

```bat
batch\25_run_B6_both_tube_interpretations.bat
```

## 9. B7 convergence

```bat
batch\26_run_B7_discretization_convergence.bat
```

This uses up to 91 discrete tubes and multiple resolutions, regularizations and bundle radii.

## 10. B8 circulation clock

```bat
batch\27_run_B8_circulation_clock.bat
```

The diagnostic clock variables are

\[
\Omega_\Gamma=\frac{\Gamma_{\rm hole}}{2\pi R_{\rm bundle}^2},
\qquad
\theta_\Gamma=\Omega_\Gamma t.
\]

## 11. Full ladder

```bat
batch\28_run_full_B0_B8_ladder.bat
```

## Result interpretation

The primary equilibrium gate is:

```text
intrinsic_residual < 0.05
```

A positive result also requires:

- valid bundle geometry;
- convergence over resolution and regularization;
- an interval of bundle strengths/radii, not one isolated tuned point;
- parity/chirality consistency;
- later confirmation with fully dynamic background tubes.
