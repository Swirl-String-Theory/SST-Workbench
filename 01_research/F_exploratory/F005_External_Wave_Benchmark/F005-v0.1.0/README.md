# F005 v0.5.0-p3 — Conditional Euler Development & Initial-State Sensitivity

**Additive development patch. NOT a new falsifier release; NOT a physically certified Euler/PKLSA comparison.**

## Installation

Extract the *contents* of this ZIP into the existing:

`01_research/F_exploratory/F005_External_Wave_Benchmark/F005-v0.1.0/`

Existing prerequisite releases: **F005 v0.4.3**, **v0.5.0** linear potential-Euler and **v0.5.0-p2** acquisition provenance audit. Keep existing `sources/`, `config/EULER_GEOMETRY_REQUIRED.json`, `outputs/`, and **DATASET.zip (49.9 GB)** unchanged. p3 does **not** open DATASET.zip. Python >= 3.10, `numpy`, `matplotlib` needed.

From PowerShell or CMD in the F005 root:

```powershell
py -3 -m pip install numpy matplotlib
.\run_all_v050_p3.cmd TEST
.\run_all_v050_p3.cmd DEMO
.\run_all_v050_p3.cmd
```

- `TEST` runs 12 synthetic regression tests, including the non-identifiability/inverse-step check and a fail-closed real-run check.
- `DEMO` creates an **entirely synthetic** output, clearly marked `DEMO_SYNTHETIC_NO_EXPERIMENTAL_VALIDATION`.
- The final command evaluates **only the 850 previously exposed v0.4.3 DEV_VALIDATION rows**, using the previously locked development split. Real source NPYs are on your PC, not in the ZIP. This step is not possible in the assistant environment without your 9,822 experiment sequences.
- A genuine normal run must find the original p2 output `outputs/f005_raw_provenance_v0.5.0_p2/p2_audit_report.json`, and the v0.4.3 split/metrics plus original robot NPY extraction. All source hashes and p2 blocking statuses are checked before accessing response rows.
- Existing `EULER_GEOMETRY_REQUIRED.json` is deliberately **never rewritten**, and E0 stays BLOCKED.

## Outputs

```
outputs/f005_conditional_euler_v0.5.0_p3/
  p3_report.json
  P3_SUMMARY.md
  p3_from_rest_metrics.csv
  p3_conditional_metrics.csv
  p3_initial_state_sensitivity.csv
  p3_initial_state_envelopes.csv
  p3_fixed_trace_sample.csv
  F005_v0.5.0-p3_LINEAR_EULER_DEVELOPMENT.pdf
```

### What is measured — exactly

* **Four-mode from-rest:** geometry-derived Euler waves driven by measured acceleration; begins at the **assumed** zero state; no measured heights used at any point in the forecast construction.
* **One-mode conditional:** only two measured heights at each predeclared anchor, known preceding acceleration to reconstruct its oscillator state, and known future acceleration; no height-feedback within the horizon.
* **Four-mode conditional minimum seed:** also uses two observed heights; six higher-mode state entries are *set to zero by assumption*, and the two remaining fundamental-mode entries are determined from the exact time-discrete observation equations. This **is not uniquely reconstructed four-mode initial data**.
* **Sensitivity:** 13 predeclared modal configurations compatible with both initial height samples, using +/-0.25 mm of individual high-mode wall displacement or +/-5 mm/s of individual high-mode wall velocity. The values are **scenario parameters, not physical uncertainty bounds**.
* **Baseline comparison:** original v0.4.3 ARX and independent oscillator aggregate scores are **read-only** and appear only beside conditional scores on the same exposed development cohort. No model fit, adjustment of geometry, reveal of test responses, or post-hoc selection based on validation errors is performed.

Anchors: `0.004 s`, `1.5 s`, `2.8 s`; horizons: `0.1`, `0.5`, `1`, `2`, `3 s`; `dt = 0.004 s`. No ARX- or oscillator-derived damping, frequency or gain enters the Euler operator.

### Recorded but explicitly unverified

- Individual `acceleration_axis_sign` and `measurement_height_sign`: **still null**; p3 uses the *relative* +1 sign hypothesis, selected on earlier TRAIN-only exploratory diagnostics, **in memory only**.
- The original per-trajectory full-fluid rest state: **unverified**. Optical offset subtraction and two close-to-zero wall-height samples do not establish no interior flow.
- Source-defined true trajectory families: missing; v0.4.3's disjoint groups are waveform-proxy graph components, and previously observed development validation rows are not blinded.
- Real flask has viscosity, meniscus/capillarity and geometric imperfections; zero-damping four-mode potential Euler is deliberately a **limiting-case diagnostic**.

## Source constraints

Documentation: `docs/P3_SCIENCE_CONTRACT.md` and `report/F005_v0.5.0-p3_Protocol.pdf` (also LaTeX source). Preserve v0.4.3/v0.5.0/p1/p2 and their source hashes, and do not change frozen TEST/OOD membership.

When you run locally, share `p3_report.json`, `P3_SUMMARY.md`, `p3_conditional_metrics.csv`, and `p3_initial_state_envelopes.csv` for an evaluation. No external work is automatically run in the background.
