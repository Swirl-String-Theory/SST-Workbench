# A058-v0.2.5 — validation and scope

## Scientific correction

- User-confirmed KnotPlot reset GUI baseline: R2 switch **OFF** and anonymous S3 strength **1.40**. These are not independently measured in this sandbox.
- R2 enabled reference: switch **ON**, S3=**1.40**; companion S4 remains at its context-measured numeric default.
- One independent matched R2 switch-OFF control at identical numeric values; separate from the continuous S3/S4 strengths.
- Design: **271** = 6 ON references + 1 OFF activation control + 8 × 33 perturbation conditions.
- Positive strength factors `2^(k/4)` for k=-16…16 and exact-zero endpoints; no fixed terminal relaxation count. Damped + collision-fast and all non-slider reset defaults unchanged.
- Install integration continues to export **exactly one** trefoil. Extra calibration probes export no curves.

## Local verification (not target KnotPlot execution)

- 24/24 unit tests PASS against a local mirror of v1.0.8 modules fetched from the user's Google Drive.
- All Python source files compile (syntax).
- 271-condition synthetic design+analysis PASS, including a separately registered R2 activation response, 264 scalar slider responses and all eight axis curves.
- Framework-v1.0.8 `validate_science_contract`, `validate_source_contract`, `validate_gate_plan`, and `validate_report`: no errors.
- Framework-v1.0.8 nonced blind terms / reveal commitments: PASS; freeze and verification on isolated copy: PASS.
- Isolated test FREEZE protocol SHA-256: `6dfacbbd7bca79621738139ae43bc368adccb0a53b6216ae56bd718359fa9909` (not a locally installed immutable protocol).
- Framework blind scan of source and synthetic generated public manifest: zero forbidden-term hits. Public campaign metadata now excludes raw switch/slider names.
- Synthetic gate-ledger diagnostic path: PASS for G0–G3, G8; G4–G7 UNRESOLVED in the synthetic test environment and do not constitute scientific evidence.
- Source ZIP is release-clean; virtual environments, build products, outputs, private run logs and frozen results are not bundled.

## Limits

- **KnotPlot live install/export/relaxation on Windows build 5125 was not run here.** The first real user-machine run must qualify the new S3=1.40 setter and R2 OFF state.
- In the current user's KnotPlot build, S3 is omitted from the `parameters` dump; `setter_acceptance` confirms only that its assignment was not rejected, **not** that internal numeric state was independently read back. This limitation is retained in provenance.
- If the R2 switch is itself getter-unreported, its OFF check similarly relies on command acceptance; the activation contrast must be treated as exploratory until independently confirmed.
- A reset-default trefoil may still fail the `safe` preflight; this version deliberately does not override `close`, `fitto`, or other geometry parameters to bypass it.
- Framework-v1.0.8 is a `LOCAL_VALIDATED_CANDIDATE` above the v1.0.7 frozen parent; hardware/SYCL certification is not claimed by these local tests.

## Target run

Place alongside v0.2.4 (never overwrite) in `01_research/A_falsifiers/A058_KnotPlot_Parameter_Sensitivity_Relaxation_Robustness/A058-v0.2.5`, with Framework-v1.0.8 installed under `06_templates/SST_Falsifier_Framework/`. Then run `cmd.exe /c run_pilot_all.cmd`.
