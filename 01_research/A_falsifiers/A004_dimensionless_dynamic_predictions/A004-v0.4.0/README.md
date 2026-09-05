# SST Dimensionless Dynamic Predictions v0.4.0

## Iso-Gamma/A dynamic-clock falsification package

This release adds a direct falsification campaign for the claim

\[
\boxed{
\text{not circulation alone, but circulation per area determines the clock rate}
}
\]

The package does **not** calculate the measured period from \(\Gamma/A\). Instead, it evolves the trefoil in the axial vortex-bundle field and extracts an observed geometric phase from the trefoil itself.

The bundle area is preregistered as

\[
A_{\rm bundle}=\pi R_{\rm bundle}^{2}.
\]

Within an iso-family, \(R_{\rm bundle}\) changes while

\[
\Gamma_{\rm hole}=\bar\zeta A_{\rm bundle}
\]

is adjusted so that

\[
\Gamma_{\rm hole}/A_{\rm bundle}=\bar\zeta
\]

remains fixed.

## Independent \(T_{\rm dyn}\) extraction

For the trefoil, the code observes the complex geometric multipole

\[
M_3(t)=
\left\langle
\left(\frac{x+iy}{r_{\rm rms}}\right)^3
\right\rangle.
\]

The orientation phase is obtained from the evolving geometry:

\[
\phi_{\rm obs}(t)=\frac{1}{3}\operatorname{unwrap}\arg M_3(t).
\]

A matched isolated trefoil run is subtracted:

\[
\Delta\Omega_{\rm dyn}
=
\Omega_{\rm bundle}^{\rm obs}
-
\Omega_{0}^{\rm obs}.
\]

The independently inferred dynamic period is

\[
T_{\rm dyn}=\frac{2\pi}{|\Delta\Omega_{\rm dyn}|}.
\]

Only afterward is the prediction tested through

\[
\boxed{
\mathcal Q_\Gamma
=
\frac{2\Delta\Omega_{\rm dyn}}{\Gamma/A}
}.
\]

The hypothesis predicts

\[
\mathcal Q_\Gamma=1.
\]

## Two gates

1. **Primary phase-rate gate.** A high-linearity fit to the directly observed initial multipole phase over a fixed time window independent of \(\Gamma/A\). It can infer a rate from a partial phase cycle and is the primary falsifier.
2. **Strict multi-cycle gate.** The full run must contain at least three measured orientation cycles. This gate is intentionally stricter and may remain inconclusive.

FFT/autocorrelation period extraction from intrinsic shape observables is reported separately and is never substituted silently when no shape period is certified.

## Included campaigns

| Config | Purpose |
|---|---|
| `C9_solid_body_positive_control.json` | extractor control; whole trefoil inside uniform-vorticity branch |
| `C9_iso_gamma_area_smoke.json` | fast physical hole-contained iso-\(\Gamma/A\) falsifier |
| `C9_iso_gamma_area_research.json` | trefoil/mirror, two resolutions, two kernels, two vorticity families |
| `C9_iso_gamma_area_discretization_smoke.json` | minimal continuum vs discrete-tube pipeline test |
| `C9_iso_gamma_area_discretization.json` | continuum vs \(N=19,37,61\) numerical representations |

## Included validation result

The positive solid-body control gives

\[
\mathcal Q_\Gamma=0.99548
\quad\text{and}\quad
1.00305,
\]

so the independent extractor correctly recovers \(\Omega=\bar\zeta/2\) when the trefoil is wholly inside a solid-body region.

For the hole-contained bundle smoke campaign, all four primary measurements are certified but give

\[
\mathcal Q_\Gamma\in[0.0210,0.0700],
\]

with a strong dependence on bundle radius despite fixed \(\Gamma/A\). Therefore:

\[
\boxed{
\texttt{ISO-GAMMA-AREA-CLOCKRATE-FALSIFIED-WITHIN-FROZEN-BUNDLE-MODEL}
}
\]

This does not falsify full 3-D backreaction, a dynamically selected area, or a proper-time bridge.

## Windows quick start

```bat
batch\01_setup_venv.bat
batch\30_iso_gamma_area_selftest.bat
batch\31_run_C9_positive_control.bat
batch\32_run_C9_iso_gamma_area_smoke.bat
```

The research campaign is started with:

```bat
batch\33_run_C9_iso_gamma_area_research.bat
```

The numerical representation check is:

```bat
batch\34_run_C9_discretization_check.bat
```

## Python CLI

```bash
python src/sst_iso_gamma_area_clock.py selftest
```

```bash
python src/sst_iso_gamma_area_clock.py campaign \
  --config configs/C9_iso_gamma_area_smoke.json \
  --output outputs/C9_iso_gamma_area_smoke
```

```bash
python tools/analyze_iso_gamma_area.py \
  --input outputs/C9_iso_gamma_area_smoke \
  --output outputs/C9_iso_gamma_area_smoke/analysis
```

## Epistemic status

\[
\boxed{[\mathrm{RESEARCH\ TRACK}]}
\]

See `docs/08_iso_gamma_area_dynamic_clock.md` and `VALIDATION_ISO_GAMMA_AREA.md`.
