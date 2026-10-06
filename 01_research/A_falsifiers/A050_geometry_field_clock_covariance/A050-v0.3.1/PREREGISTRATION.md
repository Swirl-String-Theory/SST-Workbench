# A050 v0.3.1 preregistration — diagnostic phase/frequency drift extension

## Status

Diagnostic follow-up to the completed A050 v0.3.0 real-geometry transfer run. The v0.3.0 primary verdict is immutable. This release is not a confirmatory test of a fixed m=3 hypothesis and may not rescue the parent verdict.

## Frozen parent components

The following are inherited unchanged from v0.3.0: PKLSA-qualified source panel and raw SHA-256 checks; anonymous source groups; 72-point primary curves; core ratio 0.1; time step 0.02; 2048-step modal horizon; modal qualification and persistence thresholds; five RMS-0.00125 holdouts per primary base; temporal-memory gate; spatial/divergence gates; numerical-convergence gate; and inactive Floquet/RPO policy.

## Frozen v0.3.1 diagnostic

- branch selection: existing persistence winner when available, otherwise full-horizon modal-energy maximum;
- no fixed mode number;
- active amplitude floor: 15% of trajectory maximum;
- minimum active support: 50% of samples and at least 128 samples;
- minimum total phase advance: 0.10 cycles;
- stationary linear-fit threshold: \(R^2\ge 0.90\);
- four equal phase segments, at least 32 active samples per segment;
- stationary segmented-frequency relative span: <=0.15;
- drifting quadratic-fit threshold: \(R^2\ge 0.90\);
- quadratic-over-linear BIC improvement: \(\Delta\mathrm{BIC}\ge 6\);
- instantaneous-frequency sign consistency: >=0.90;
- residual autocorrelation screen: lags 1..8, maximum absolute residual ACF <= \(2.5/\sqrt{N}\);
- primary diagnostic support threshold: coherent classification on at least 3/5 primary baselines;
- holdouts remain within-base robustness diagnostics and are not counted as independent baselines.

The classifier reports `STATIONARY_COHERENT`, `COHERENT_DRIFTING`, or `INCOHERENT_OR_UNRESOLVED`. These labels are diagnostic and do not enter the v0.3.0 primary PASS/FAIL logic.

The v0.3.1 operative files are cryptographically sealed in `config/SEAL_v0.3.1.json` before the diagnostic rerun.
