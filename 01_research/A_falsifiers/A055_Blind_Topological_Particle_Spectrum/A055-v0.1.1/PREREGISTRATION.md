# PREREGISTRATION — A055 v0.1.1

## 1. Frozen population

All 82 supplied atlas objects are included:

- 35 non-trivial prime knots, crossing number 3–8;
- 47 prime links, crossing number 2–8.

No topology may be added, removed or promoted using historical SST/VAM labels or Standard-Model masses.

## 2. Blind exclusion

The BLIND measurement stage must not read:

- `reveal/historical_hypotheses.json`;
- `reveal/sm_reference_2026.json`.

Opaque case IDs are HMAC-SHA256 values generated from a fresh run-local secret.  The secret and topology mapping are stored only under `PRIVATE_REVEAL_DO_NOT_INCLUDE_IN_BLIND/`.

## 3. Resolution and presentation qualification

Normal presets use

\[
N=40,80,160
\]

points per component.

For a feature \(X\), define

\[
\delta_X=
\frac{|X_{160}-X_{80}|}
{\max(|X_{160}|,|X_{80}|,10^{-15})}.
\]

At \(N=160\), define the presentation coefficient of variation

\[
CV_X=\frac{\sigma_X}{|\bar X|+10^{-15}}.
\]

The `basic` gate is

\[
\delta_X\le0.20,\qquad CV_X\le0.50,
\]

using 8 embedding replicates/resolution.

The `full` gate is

\[
\delta_X\le0.15,\qquad CV_X\le0.35,
\]

using 16 embedding replicates/resolution.

A feature that fails either gate is unavailable to the qualified search for that case.

## 4. Frozen primary features

Primary screening features:

1. `bend_energy`;
2. `abs_neumann_energy`;
3. `min_distance`;
4. `abs_writhe`;
5. `linking_strength` (links only).

`contact_ratio=min_distance/mean_segment` is diagnostic only and may not contribute to pair ranking or ratio fitting because it changes explicitly with segmentation resolution.

## 5. Frozen feature domains

| feature | knots | links | mixed all-atlas |
|---|---:|---:|---:|
| `bend_energy` | yes | yes | yes |
| `abs_neumann_energy` | yes | yes | yes |
| `min_distance` | yes | yes | yes |
| `abs_writhe` | yes | yes | no |
| `linking_strength` | no | yes | no |
| `contact_ratio` | no | no | no |

`linking_strength` for knots is not zero-valued data; it is **not an applicable observable**.

## 6. Frozen blind pair spaces

The `common_all` space contains all 82 cases and uses

\[
\{E_{\rm bend},|E_N|,d_{\min}\}.
\]

The knot-only space uses

\[
\{E_{\rm bend},|E_N|,d_{\min},|Wr|\}.
\]

The link-only space uses

\[
\{E_{\rm bend},|E_N|,d_{\min},|Wr|,L_{\rm strength}\}.
\]

For each feature, pair-space transformation is

\[
y=\operatorname{asinh}\!\left(\frac{|X|}{\operatorname{median}(X_{>0})}\right)
\]

followed by z-standardization.  The pair distance is Euclidean in the resulting feature space.

Raw tables are diagnostic.  Qualified tables retain only cases whose required features pass Section 3.

## 7. Historical `5_2/6_1` reveal gate

The historical hypothesis is opened only after the BLIND tree is SHA-256 sealed.

A scientific historical rank is assigned only if both `5_2` and `6_1` occur in the qualified knot pair table.  Otherwise the result is `NOT_QUALIFIED`; any raw rank is reported only as a diagnostic.

## 8. Frozen mass-ratio algebra

For each allowed positive feature \(X\), only one multiplicative scale is fitted:

\[
m_i\approx sX_i,
\qquad
\ln s=\frac{1}{3}\sum_i(\ln m_i-\ln X_i).
\]

The registered error is

\[
\epsilon_{\log}
=
\sqrt{\frac{1}{3}\sum_i
\left[\ln(sX_i)-\ln m_i\right]^2}.
\]

Values \(X\le10^{-12}\) are excluded from logarithmic ratio fitting.  They are not replaced by a positive numerical floor.

No powers, roots, offsets, \(\pi\), \(2\pi\), \(\alpha\), golden-ratio terms or other post-reveal transformations may be introduced.

## 9. Look-elsewhere null

For a target triplet with fixed log-span \(S\), null targets are

\[
(0,tS,S),\qquad t\sim U(0,1).
\]

Each valid search uses 10,000 deterministic pseudo-random values generated from the preregistered `null_seed` and group offset.

For every \(t\), the complete eligible triplet population is searched.  The implementation may accelerate this calculation algebraically, but the returned minimum must equal the brute-force triplet minimum to numerical tolerance.

The empirical one-sided null fraction is

\[
p_{\rm null}=
\frac{1+\#\{\epsilon_{\rm null}\le\epsilon_{\rm observed}\}}
{1+N_{\rm null}}.
\]

Three multiplicity layers are frozen:

- **within-search**: the null repeats the full topology-triplet search for one fixed feature and topology pool;
- **group-familywise**: for each null draw, take the minimum error across all valid preregistered feature/pool searches in that SM group; a separate `common_all` familywise statistic is also reported;
- **global SM search**: for each trial index, take the minimum of the group-familywise null errors across every preregistered SM triplet group.

Thus a highlighted best match may not quote the less conservative within-search value as though it were a global discovery p-value.

## 10. Kill / promotion criteria

v0.1.1 cannot establish a particle identity.  It may only:

- reject a screening adjacency claim;
- mark a candidate or feature `NOT_QUALIFIED`;
- show that an apparent SM ratio is generic under the null;
- identify stable candidates worth promotion to PKLSA/finite-core dynamics.

A055 v0.2.0 must preserve the blind/reveal split, feature-domain discipline, convergence qualification and null treatment while replacing PD-derived screening geometry with physically stronger dynamical observables.
