# A050 v0.3.1 — Nonstationary Phase/Frequency Drift Diagnostic

This release is a copy-on-write diagnostic extension of A050 v0.3.0. It keeps the frozen PKLSA real-geometry source panel, dynamics, modal-persistence thresholds, pressure-memory thresholds, numerical-convergence logic, and source-blindness rules unchanged.

## Scientific question

The v0.3.0 transfer run repeatedly selected the same transverse branch while failing the strict persistence criterion on frequency stability. v0.3.1 asks a narrower question: is the apparent branch genuinely incoherent, or is it a coherent but nonstationary phase trajectory whose instantaneous frequency drifts over the 2048-step window?

The diagnostic does **not** hard-code a mode number. The branch is chosen blind from the existing persistence winner when available, otherwise from the full-horizon modal-energy maximum. Any later observation that this branch is often m=3 is descriptive, not an acceptance target.

## Diagnostic classifier

For the selected complex modal coefficient \(z(t)\), the active-amplitude phase \(\phi(t)=\operatorname{unwrap}(\arg z(t))\) is compared under two nested descriptions:

\[
\phi_{\rm lin}(t)=a_0+a_1 t,\qquad
\phi_{\rm quad}(t)=b_0+b_1 t+b_2 t^2.
\]

The quadratic model is treated as evidence for coherent drift only when it gives a material Bayesian-information-criterion improvement, the phase remains directionally consistent, segmented frequency is inconsistent with the stationary tolerance, and the quadratic residual passes the frozen autocorrelation screen. A stationary classification requires a strong linear fit, frequency consistency across four segments, and a corresponding residual screen.

The three output classes are `STATIONARY_COHERENT`, `COHERENT_DRIFTING`, and `INCOHERENT_OR_UNRESOLVED`.

## Integrity rule

v0.3.1 is diagnostic because its question was motivated by the observed v0.3.0 failure pattern. It cannot convert a v0.3.0 modal-transfer FAIL into PASS. `blind_results.json` therefore replays the v0.3.0 primary acceptance logic unchanged and stores the new result separately under `nonstationary_phase_diagnostic`.

Primary aggregation uses only the five independent primary baselines; perturbation holdouts are reported per carrier but are not counted as independent evidence for the diagnostic majority.

## Run

From `A050-v0.3.1`:

```bat
run_all.cmd
```

The output folder is `SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.3.1-outputs`. Freeze/hash the BLIND archive before `run_reveal.cmd`.
