# F005 v0.4.2 — Frozen science contract (DEVELOPMENT)

## Source identity / anti-peeking

Input: `INPUT_TRAIN.npy` [m/s^2]; output: `OUTPUT_TRAIN.npy` [mm]; time vector [s], dt 0.004 s. Source is the Giulietti et al. robot sloshing Zenodo dataset (10.5281/zenodo.20039757).

Use the unchanged candidate partition from v0.2.0: TRAIN 3500, VALIDATION 750, TEST 750, OPTIMIZED_OOD 4822. Source integrity is checked against v0.3.0 audit and v0.4.1 experiment, including the input-array hash and VALIDATION-ONLY output subset hash. TEST/OOD output arrays must not be accessed. The 49.9GB `DATASET.zip` is never read.

## Model and forcing

Frozen ARX(2):

`eta[n+1] = A*eta[n] + B*eta[n-1] + C*(dt^2)*a[n]`

where eta is in **m**, a in **m/s^2**, dt in **s**, and A,B,C dimensionless.
A = 1.9856661039519918, B = -0.9908696423084401, C = -1.118156917616826. Exact values loaded from frozen v0.3 audit, never fitted to VALIDATION.

At each predetermined anchor t0 in {0.004,1.5,2.8}s, use exactly two measured elevations (t0-dt,t0), then only recursively predicted heights. Future input acceleration a[n] is supplied as **known**, not forecast. Horizons 0.1,0.5,1,2,3s.

## Observables

Path RMSE (for a given horizon H and N validation trajectories) computed from all j=1..H/dt:

`RMSE_path = sqrt(mean_i,j((eta_pred[i,j] - eta_obs[i,j])^2))`.

Endpoint RMSE is `sqrt(mean_i((eta_pred[i,H] - eta_obs[i,H])^2))`.
All reported RMSE are converted to **mm**. Bootstrap CI on difference (zero-response RMSE minus ARX RMSE) uses seed 20261020 and 400 trajectory resamples; not group-independent.

Baselines (all predeclared, no fit on VALIDATION):
- persistence eta(t0);
- linear extrapolation from the two origin heights;
- zero equilibrium eta=0;
- unforced damped oscillator with TRAIN-derived gamma, f_d from frozen ARX poles; no future forcing. The oscillator parameters are NOT independently fit from an Euler/PDE solver.

For phase/amplitude exploratory checks, project measured/predicted demeaned time series onto fixed `f_d` harmonic; record median phase error and amplitude ratio if horizon >= max(0.5s, one period) and measured projected amplitude >=0.25mm. These quantities are not mode-identification evidence.

## Family screening & falsifier gates

- P5c: all pairs emitted by the three v0.4.1 input fingerprints and neighbor proposal rule are scored using corr >= .995 and normalized RMSE <= .075 with time shifts {-4,-2,0,2,4} samples. This candidate generator does not search all n(n-1)/2 pairs and is not a publisher family lookup. No independence certification.
- P6d/e: descriptive validation only, no TEST/OOD outcomes and no model refit.
- P6g: derive input-shape connected components; flag VALIDATION rows with a matching path to TRAIN. Evaluate a *screen-negative* subset (when nonempty) as a sensitivity check, not a new holdout or group-independent certification.
- P7: source-native Euler/PKLSA NOT RUN; P8: physical claims UNRESOLVED.

A family-disjoint blind gate requires source-defined family IDs or an independently justified complete generator family mapping and a registered locked split created before holdout reveal. Do not upgrade P5c/P6g from `REVIEW/BLOCKED` based on high correlations or small RMSE.

## References (copy-ready LaTeX)

```latex
\bibitem{Giulietti2026Sloshing}
Giulietti et al.,
``Robot-executed sloshing dataset,''
Zenodo (2026).
\url{https://doi.org/10.5281/zenodo.20039757}.

\bibitem{Ljung1999}
L.~Ljung, \emph{System Identification: Theory for the User},
2nd ed., Prentice Hall (1999), ISBN 9780136566953.
```
