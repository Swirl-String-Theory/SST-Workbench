# Validation — C9 iso-Γ/A dynamic clock

## Software validation

- Unit tests: **18/18 pass**.
- Synthetic complex multipole with known angular rate: recovered to floating-point precision.
- Synthetic scalar oscillator: period recovered by FFT/autocorrelation consensus.
- Constant scalar signal: correctly rejected as `NO_SHAPE_OSCILLATION`.
- Iso-family construction: \(\Gamma/A\) remains fixed to numerical precision while radius changes.

## Positive control

Configuration: `configs/C9_solid_body_positive_control.json`.

The bundle is deliberately larger than the entire trefoil, so every trefoil point lies in the uniform-vorticity Rankine branch. This is a mathematical extractor control, not the physical central-hole model.

Measured results:

| Sign | \(\mathcal Q_\Gamma\) | standard error | Verdict |
|---:|---:|---:|---|
| \(-\) | 1.0030489 | 0.0007014 | PASS |
| \(+\) | 0.9954781 | 0.0009923 | PASS |

Thus the independent phase extractor correctly recovers

\[
\Delta\Omega_{\rm dyn}=\frac{\Gamma/A}{2}
\]

when the geometric conditions for solid-body rotation are actually satisfied.

## Hole-contained iso-Γ/A smoke test

Configuration: `configs/C9_iso_gamma_area_smoke.json`.

Common prescribed value:

\[
|\Gamma/A|=128.
\]

The bundle is contained inside the free central aperture. The trefoil itself therefore samples primarily the exterior field rather than the uniform-vorticity interior.

| sign | \(R_{\rm bundle}/R_{\rm hole}\) | \(\mathcal Q_\Gamma\) | stderr | certified |
|---:|---:|---:|---:|---|
| \(-\) | 0.5 | 0.0210370 | 0.0000244 | yes |
| \(-\) | 0.9 | 0.0673999 | 0.0003133 | yes |
| \(+\) | 0.5 | 0.0211181 | 0.0000160 | yes |
| \(+\) | 0.9 | 0.0700195 | 0.0003692 | yes |

All four primary phase-rate measurements satisfy the extraction-quality gates. All four violate

\[
|\mathcal Q_\Gamma-1|<0.02.
\]

Moreover, at fixed \(\Gamma/A\), changing the bundle radius changes \(\mathcal Q_\Gamma\) by about 0.046–0.049. This independently violates the preregistered iso-family spread threshold of 0.02.

## Numerical representation smoke test

At resolution 32, \(R_{\rm bundle}/R_{\rm hole}=0.9\), \(\Gamma/A=128\):

| representation | \(\mathcal Q_\Gamma\) |
|---|---:|
| continuum Rankine | 0.0716133 |
| discrete \(N=7\) | 0.0716595 |

The difference is approximately \(4.6\times10^{-5}\), showing that the conclusion is not produced by the continuum-only code path in this control.

## Scientific verdict

\[
\boxed{
\text{Bundle-average }\Gamma/A\text{ is not sufficient to determine the observed trefoil clock rate}
}
\]

within the implemented frozen straight axial-bundle model.

What survives is the narrower statement:

\[
\Gamma/A=\bar\zeta,
\qquad
\Omega=\bar\zeta/2
\]

for material points that actually lie in a uniform-vorticity solid-body region, or for the boundary-average associated with the same contour and area.

## Open gates

- dynamically evolving/background tubes;
- mutual trefoil–tube induction;
- dynamically selected clock surface;
- stable recurrent trefoil–bundle state;
- derivation connecting the phase clock to proper time.
