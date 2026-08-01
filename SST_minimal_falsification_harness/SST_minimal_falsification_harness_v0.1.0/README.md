# SST Minimal Falsification Harness

This package implements a strict version of the proposed route

\[
\alpha^{-1}
=
\frac{8\pi}{3}\mathcal L_D
+
\Delta[\kappa,\Omega_3,\mathcal C_{\rm contact},f].
\]

The program does **not** fit the trefoil correction to \(\alpha\). It first fits a declared EFT truncation to independent observables, freezes the coefficients, and only then compares the trefoil prediction with

\[
\Delta_{\rm target}
=
\alpha^{-1}
-
\frac{8\pi}{3}\mathcal L_D.
\]

## What it tests

The implemented linear truncation is

\[
\Delta
=
c_L F_L
+
c_\kappa F_\kappa
+
c_\Omega F_\Omega
+
c_C F_C,
\]

with default features

\[
F_L=\mathcal L_D,\qquad
F_\kappa=\int(D\kappa)^2\,\frac{ds}{D},\qquad
F_\Omega=\int(D\Omega_3)^2\,\frac{ds}{D},
\]

and a finite nonlocal contact-shell proxy \(F_C\).

The basis can be changed in the calibration JSON. Each independent observable must provide the design-row coefficients showing how the same Wilson coefficients enter that observable.

## Verdicts

- `INCONCLUSIVE_UNDERDETERMINED`  
  The calibration is leaky, rank-deficient, poorly conditioned, lacks residual degrees of freedom, or fails leave-one-out validation. This does **not** falsify SST; it falsifies the claim that the present route is independently predictive.

- `FALSIFIED_AT_DECLARED_TOLERANCE`  
  Independent calibration passes, coefficients are frozen, and the trefoil prediction misses the preregistered target.

- `TREFOIL_MATCH_BUT_CROSS_OBSERVABLE_FAILURE`  
  The trefoil happens to match, but independent holdouts fail.

- `NOT_FALSIFIED`  
  Calibration, leave-one-out, trefoil prediction, and holdouts all pass. This is survival of the test, not proof.

## Quick start

### 1. Verify the software pipeline with synthetic data

The demo is explicitly nonphysical.

```bash
python sst_minimal_falsification.py demo --calibration-out synthetic_calibration.json --geometry-out synthetic_geometry.json

python sst_minimal_falsification.py audit --calibration synthetic_calibration.json --geometry synthetic_geometry.json --out synthetic_report.json --abs-tol 1e-3
```

### 2. Create an independent-calibration template

```bash
python sst_minimal_falsification.py template --out calibration_template.json
```

Replace every `REPLACE` field. Do not use \(\alpha\), the final target correction, the elementary charge, or a swirl speed already calibrated through \(\alpha\).

### 3. Extract trefoil geometry features

For a centerline file:

```bash
python sst_minimal_falsification.py geometry --curve-csv ideal_trefoil.csv --diameter 1.0 --samples 2000 --core-profile gaussian --gaussian-width 0.25 --out ideal_trefoil_features.json
```

The CSV must contain:

```text
x,y,z
...
```

If the coordinates are already normalized to tube diameter \(D=1\), use `--diameter 1.0`.

A material-frame twist file may be added:

```bash
--twist-csv omega_hat.csv
```

with column:

```text
omega_hat
...
```

Here \(\omega_{\rm hat}=D\Omega_3\).

### 4. Run the falsification audit

```bash
python sst_minimal_falsification.py audit --calibration calibration_filled.json --geometry ideal_trefoil_features.json --out falsification_report.json --abs-tol 1e-3 --max-z 3 --max-reduced-chi2 3
```

The tolerance must be chosen before examining the trefoil result.

## Calibration JSON

Each row is one independent equation

\[
y_n = \sum_a A_{na}c_a+\epsilon_n.
\]

Example:

```json
{
  "id": "ring_energy_R1",
  "role": "calibration",
  "observable": "dimensionless ring-energy matching datum",
  "value": 0.0123,
  "sigma": 0.0004,
  "features": {
    "length": 1.0,
    "bend": 0.25,
    "twist": 0.0,
    "contact": 0.0
  },
  "provenance": {
    "source": "simulation or experiment identifier",
    "derivation": "equation mapping this datum to the Wilson basis",
    "used_constants": ["list all inputs"]
  }
}
```

A holdout row uses `"role": "holdout"` and is never used in fitting.

## Essential methodological restriction

Ring energy, ring speed, Kelvin dispersion, and contact response are different observables. They can calibrate a common Wilson basis only after their forward equations have been derived. Entering arbitrary geometry numbers as design rows would be curve fitting, not EFT matching.

## Geometry warning

The built-in `trefoil`, `figure8`, and `cinquefoil` curves are smooth smoke-test embeddings. They are not ideal-knot minimizers. For a quantitative test, provide the high-resolution centerline and its independently fixed tube diameter.

## Recommended gate sequence

1. No target-coupling leakage.
2. At least \(p+1\) calibration rows for \(p\) coefficients.
3. Full-rank and well-conditioned design matrix.
4. Acceptable reduced \(\chi^2\).
5. Leave-one-out validation.
6. Frozen trefoil prediction.
7. Independent holdout validation.

## References

```latex
\begin{thebibliography}{99}

\bibitem{Saffman1992}
P.~G. Saffman,
\emph{Vortex Dynamics},
Cambridge University Press (1992),
doi:10.1017/CBO9780511624063.

\bibitem{HornNicolisPenco2015}
B.~Horn, A.~Nicolis, and R.~Penco,
``Effective string theory for vortex lines in fluids and superfluids,''
\emph{JHEP} \textbf{10}, 153 (2015),
doi:10.1007/JHEP10(2015)153,
arXiv:1507.05635.

\bibitem{PrzybylPieranski2014}
S.~Przybyl and P.~Pieranski,
``High resolution portrait of the ideal trefoil knot,''
\emph{J. Phys. A} \textbf{47}, 285201 (2014),
doi:10.1088/1751-8113/47/28/285201,
arXiv:1402.5760.

\end{thebibliography}
```