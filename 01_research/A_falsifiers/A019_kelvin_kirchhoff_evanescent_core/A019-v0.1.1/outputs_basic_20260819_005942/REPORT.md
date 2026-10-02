# Kelvin–Kirchhoff SST blind falsifier report

Campaign mode: **basic**

Cases: **8** — PASS 0, FAIL 8, INCONCLUSIVE 0

## Interpretation boundary

- The numerical runner uses only the relaxed centerlines, their Ridgerunner thickness metadata, a fixed regularized Biot–Savart model, and preregistered numerical settings.
- It does **not** identify the Ridgerunner tube thickness with SST `r_c`; the current Canon explicitly keeps resolved tube/core thickness separate from the horn/circulation radius.
- A failure falsifies this **Kelvin-inspired centerline closure on the tested geometry/model**, not SST as a whole.
- Kirchhoff detailed balance is reported as `NOT_TESTABLE`: centerline geometry contains no equilibrium mode-resolved incident, absorbed, and emitted fluxes. The package deliberately does not invent a proxy.

## Gates

1. **Geometry QC** — checks the supplied Ridgerunner residual/edge uniformity and provenance of the smoothing radius.
2. **Relative equilibrium** — asks whether self-induced velocity is well approximated by one rigid translation plus one rigid rotation.
3. **Kelvin 2Ω gap** — extracts a spectrum from a finite-difference linearization, fits `sigma^2 = sigma0^2 + c_eff^2 k^2` on a training subset, predicts held-out modes, and only afterward tests `sigma0/(2 Omega_eff) = 1`.
4. **Evanescent confinement** — measures the radial decay of a perturbation response and only afterward compares the fitted decay length with `c_eff/(2 Omega_eff)`; an exponential must also beat a power law by the preregistered AIC margin.
5. **Kirchhoff detailed balance** — not testable from these data alone.

## Results

| Dataset | Overall | RelEq | Gap | Evanescent | gap/(2Ω) | Lobs/Lpred |
|---|---:|---:|---:|---:|---:|---:|
| knot_3.1_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_4.1_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_6.2_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_6.3_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_7.2_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| torus_2.3_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| torus_2.4_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | 0 | 3.2853 |
| torus_2.8_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | 0.6917 | — |

## Files

- `unblinded_summary.csv` — compact machine-readable result table.
- `blind_campaign/results/CASE_*/raw.json` — target-free extracted observables.
- `blind_campaign/results/CASE_*/spectrum.csv` — eigenvalue/frequency/wavenumber rows.
- `blind_campaign/results/CASE_*/operator_A.npy` — projected linearized operators.
- `blind_campaign/results/frozen_preregistration.json` — thresholds frozen before case results.
- `private_blind_key.json` — identity mapping kept outside the blind campaign.
