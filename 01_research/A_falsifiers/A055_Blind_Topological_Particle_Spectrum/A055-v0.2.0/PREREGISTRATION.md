# PREREGISTRATION — A055 v0.2.0

## Population

The atlas remains frozen at 82 prime objects:
- 35 knots with crossing number 3–8;
- 47 prime links with crossing number <=8.

No topology is added or removed after reveal.

## Blind exclusions

The BLIND stage must not read:
- `reveal/historical_hypotheses.json`;
- `reveal/sm_reference_2026.json`.

The historical `5_2/6_1` mapping is not a dynamic selection criterion.

## Production source gate

A knot may enter C006 dynamics only when E011-v0.3.0 supplies exactly one `STATIC_READY` anchor for every preregistered provider group (`gilbert`, `knotplot` by default).

Provider source bytes are hashed. E011-certified ropelength defines \(D_{\rm eff}=1\).

## Frozen knot dynamics

The C006 closure is used without a parameter scan:

\[
\text{offset}/D=0.25,\quad \epsilon/D=0.10,\quad
\Gamma_+=+1,\quad \Gamma_-=-1,\quad
\phi_{\rm channel}=\pi/2.
\]

These are method parameters and contain no SM mass or SST particle target.

Quick:
\[
N=(24,32,40),\quad m=1,2,3.
\]

Full:
\[
N=(40,56,72,88),\quad m=1,\ldots,5.
\]

Branch identity requires eigenvector overlap >=0.80 and the preset eigenvalue-shift tolerance.

## RPO gate

The RPO search uses exactly the same generator parameters. No scan over offset, core size, phase or circulation signs is permitted.

## True-Floquet gate

The full campaign uses C006 relative-return monodromy only after RPO/cross-provider qualification. Frozen thresholds:

- \(N_F=20\), with C006 hard maximum \(N\le24\);
- base return residual <=0.06;
- time-tangent neutral residual <=0.30;
- Kelvin-subspace leakage <=0.40;
- maximum multiplier modulus deviation from unity <=0.25.

These thresholds are frozen before the first A055-v0.2.0 scientific run and are not target-fitted.

## Link policy

Links cannot enter dynamic particle fits in v0.2.0. This is a hard fail-closed boundary until a separately validated multi-component C006-equivalent contract exists.

## Reveal observables

Only particle-promotion-qualified knots may enter the mass-pattern layer. Preregistered scalar observables are:

1. E011 ropelength;
2. \(\hat\omega_{m=1}\);
3. \(\hat\omega_{m=2}\);
4. \(\hat\omega_{m=3}\).

Only one multiplicative scale may be fitted for a three-state mass family.

No powers, roots, \(\pi\)-factors, \(\alpha\)-factors, golden-ratio factors, offsets or topology-specific parameters may be introduced after reveal.

Mass-pattern effect-size gate:

\[
\epsilon_{\log}\le0.25.
\]

Null searches use 10,000 randomized intermediate log-mass positions for production. Multiple testing is corrected hierarchically over the preregistered observables and SM groups.

## Higgs boundary

The W/Z/H group is a mass-pattern test only. A Higgs claim additionally requires an independently preregistered scalar-mode/coupling gate, which is absent in v0.2.0.
