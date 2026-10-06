# PREREGISTRATION — A054 v0.1.0

## Frozen blind population

All 82 supplied atlas objects are included:
- 35 non-trivial prime knots, crossing number 3–8;
- 47 prime links, crossing number 2–8.

No topology is promoted or removed based on the historical SST mapping or SM masses.

## Blind exclusion

The blind stage must not read:
- `reveal/historical_hypotheses.json`
- `reveal/sm_reference_2026.json`

Opaque case IDs are HMAC-SHA256 values generated from a fresh run-local secret. The secret and topology mapping are written only to `PRIVATE_REVEAL_DO_NOT_INCLUDE_IN_BLIND/`.

## Frozen screening features

Primary positive feature set:
1. `bend_energy`
2. `abs_neumann_energy`
3. `contact_ratio`
4. `abs_writhe`
5. `linking_strength`

Pair-neighbor distance is Euclidean distance after log-transform and z-standardization of these five features.

## Reveal search algebra

For a positive scalar feature \(X\), only a single free multiplicative scale is allowed when comparing three topology values with a three-particle mass family:

\[
m_i \approx s\,X_i,
\qquad
\ln s = \frac{1}{3}\sum_i (\ln m_i-\ln X_i).
\]

The registered error is

\[
\epsilon_{\log}
=
\sqrt{\frac{1}{3}\sum_i
\left[\ln(sX_i)-\ln m_i\right]^2}.
\]

No powers, roots, factors of \(\pi\), \(\alpha\), golden-ratio factors, or hand-selected offsets may be added after reveal.

## Null diagnostic

For each target mass family and total mass span, the intermediate target is randomized uniformly in log-position. Each null target repeats the complete atlas triplet search. The fraction of null targets whose best fit is at least as good as the real target is reported.

## Kill criteria

v0.1.0 cannot establish an SM assignment. It can only:
- reject the historical pair as non-special in the frozen screening space;
- identify candidates for promotion;
- show that a claimed mass pattern is generic under the look-elsewhere null;
- or justify a v0.2.0 PKLSA/finite-core dynamical test.
