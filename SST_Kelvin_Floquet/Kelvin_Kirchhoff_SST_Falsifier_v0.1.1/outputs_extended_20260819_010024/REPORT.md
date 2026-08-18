# Kelvin–Kirchhoff SST blind falsifier report

Campaign mode: **extended**

Cases: **49** — PASS 0, FAIL 23, INCONCLUSIVE 26

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
| knot_0.1_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_10.123_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_10.1_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_3.1_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_4.1_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_5.1_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_5.2_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_6.1_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_6.2_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_6.3_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_7.1_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_7.2_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_7.3_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_7.4_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_8.17_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_8.18_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_8.1_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_9.1_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_9.2_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| knot_9.35_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | — | — |
| link_0.2.1_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | — | — |
| link_0.3.1_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | 0 | 3.1379 |
| link_2.2.1_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | — | — |
| link_4.2.1_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | — | — |
| link_5.2.1_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| link_6.2.1_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | 1.7736 | — |
| link_6.3.1_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | — | — |
| link_6.3.2_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | — | — |
| link_6.3.3_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | — | — |
| link_7.2.5_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | — | — |
| link_7.2.6_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | — | — |
| link_7.2.8_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | — | — |
| link_8.2.1_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | — | — |
| link_9.2.20_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | — | — |
| link_9.2.40_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | — | — |
| torus_2.11_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| torus_2.3_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| torus_2.4_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| torus_2.5_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| torus_2.6_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | 0.7816 | — |
| torus_2.7_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| torus_2.8_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | 0.17301 | 2.7848 |
| torus_2.9_final.txt | FAIL | FAIL | INCONCLUSIVE | INCONCLUSIVE | — | — |
| torus_3.3_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | — | — |
| torus_3.6_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | 0 | 1.8896 |
| torus_3.9_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | 0 | 3.9958 |
| torus_6.15_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | 0 | 5.1649 |
| torus_6.21_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | 0.55399 | 2.7777 |
| torus_6.9_final.txt | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | 0 | 1.8564 |

## Files

- `unblinded_summary.csv` — compact machine-readable result table.
- `blind_campaign/results/CASE_*/raw.json` — target-free extracted observables.
- `blind_campaign/results/CASE_*/spectrum.csv` — eigenvalue/frequency/wavenumber rows.
- `blind_campaign/results/CASE_*/operator_A.npy` — projected linearized operators.
- `blind_campaign/results/frozen_preregistration.json` — thresholds frozen before case results.
- `private_blind_key.json` — identity mapping kept outside the blind campaign.
