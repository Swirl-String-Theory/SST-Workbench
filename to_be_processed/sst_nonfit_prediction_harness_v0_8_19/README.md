# SST Non-Fitted Prediction Harness v0.8.19 draft

Research-track harness for reporting the four SST closure gates as explicit status fields:

1. `i_topological_mass_kernel_closure`
2. `ii_non_fitted_prediction_protocol`
3. `iii_spinorial_boundary_theta_pi`
4. `iv_core_torsion_impedance_matching`

The harness is intentionally outside `SSTcore`. It is a protocol/audit layer, not a canonized API.

## Status values

```text
DERIVED
CALIBRATED
RESEARCH_TRACK
FAILED
NOT_AVAILABLE
```

## Main equations

```text
lambda_c = 2*pi*c*r_c / v_swirl
M0[K] = 2*pi^3*rho_m*r_c^5*Ltot[K]/lambda_c^2
M[K] = (lambda_c/(pi*r_c))^G * Xi_K * M0[K]
chi_K^(T) = c^2*lambda_iso(M_torsion[K])/(2 E0[K])
```

## Run demo

```bash
python nonfit_harness.py
```

Outputs:

```text
out/nonfit_report.json
out/nonfit_gates.csv
```

## Run against an SSTcore ideal.txt

```bash
python nonfit_harness.py  --knot-id 3:1:1  --ideal C:\workspace\projects\SST-Workbench\knots_ideal_favorites.txt  --out-json out/trefoil_nonfit_report.json
```

## Include the standalone torsion-impedance audit

```bash
python nonfit_harness.py  --knot-id 3:1:1  --torsion-json C:\workspace\projects\SST-Workbench\to_be_processed\sst_torsion_impedance_pybind11_v0.8.19_autobuild\sst_torsion_impedance_pybind11_v0_8_19\impedance_results.json   --torsion-density-key rho_f
```

## Negative controls

These should fail strict non-fitted mode:

```bash
python nonfit_harness.py --use-target-mass-as-input
python nonfit_harness.py --use-required-kernel-as-input
```

Use `--allow-calibration` only when deliberately producing a calibrated benchmark rather than a non-fitted prediction.

## Design notes

The mass-kernel gate reports required values such as `required_Xi_for_target_not_used`, but does not feed them back into the prediction. If a post-hoc kernel or target mass is used as an input, the relevant gate is marked `FAILED` in strict mode.

The torsion gate reads JSON produced by the separate `sst_torsion_impedance_pybind11` package. Required impedance/density fields from that package are diagnostics only; using them as inputs violates the non-fitted protocol.