# SST Independent Calibration Upgrade — v0.3.0

## Verdict on the existing JSON

`independent_calibration_plan_v0.1.json` is scientifically useful as a
**campaign specification**. It is not yet a calibration file accepted by the
falsification harness because it contains:

- parameter campaigns rather than individual numerical rows;
- no independently calculated response residuals;
- no numerical uncertainties;
- no solver-output provenance.

The new upgrader converts the plan into concrete rows while enforcing

\[
c_L=0
\]

and the minimal response truncation

\[
\Delta
=
c_\kappa I_{\kappa^2}
+
c_\Omega I_{\Omega^2}
+
c_C C_{\rm contact}.
\]

## Stage 1 — generate the v2 draft

```bash
python upgrade_calibration_json.py generate ^
  --plan independent_calibration_plan_v0.1.json ^
  --out calibration_v2_draft.json ^
  --results-template calibration_results_template.csv
```

PowerShell one-line version:

```powershell
python upgrade_calibration_json.py generate --plan independent_calibration_plan_v0.1.json --out calibration_v2_draft.json --results-template calibration_results_template.csv
```

The generated rows are:

- four circular-ring bend calibrations;
- four straight-periodic twist calibrations;
- five antiparallel-periodic contact calibrations;
- one twisted-ring mixed holdout;
- one unseen-separation contact holdout.

The geometry features are calculated automatically.

## Stage 2 — fill the results CSV

Fill either `value` or `R_micro` for every row.

When `R_micro` is supplied, the upgrader computes

\[
\texttt{value}
=
\mathscr R_{\rm micro}
-
\frac{8\pi}{3}\mathcal L_D.
\]

Also supply:

- `sigma`;
- `source`;
- `derivation`;
- `used_constants`, separated by semicolons.

Do not enter \(\alpha\), the elementary charge, the target correction, or a
swirl speed calibrated through \(\alpha\).

## Stage 3 — finalize

```powershell
python upgrade_calibration_json.py finalize --draft calibration_v2_draft.json --results calibration_results_template.csv --out calibration_filled_v2.json
```

The command refuses to finalize when:

- required values or uncertainties are absent;
- provenance is absent;
- forbidden evidence appears;
- the design matrix is rank-deficient.

The result is directly accepted by:

```powershell
python sst_minimal_falsification.py audit --calibration calibration_filled_v2.json --geometry gilbert_trefoil_features.json --out falsification_report.json --abs-tol 0.001
```

## Legacy cleanup

An old calibration JSON containing `length` can be sanitized:

```powershell
python upgrade_calibration_json.py sanitize-legacy --input calibration_old.json --out calibration_old_sanitized_v2.json
```

This only removes the degenerate length feature. It does not invent missing
microscopic results.

## Why the length coefficient is removed

Allowing

\[
\Delta=c_L\mathcal L_D+\cdots
\]

changes the leading coefficient into

\[
\frac{8\pi}{3}+c_L.
\]

Then \(c_L\) can absorb the trefoil discrepancy by construction. Fixing
\(c_L=0\) is therefore a necessary renormalization condition for an independent
test.
