# Preregistration — SST Threaded-Hole Substrate v0.2.0

## Primary separation of claims

The following hypotheses are independent:

- **H-SC:** active hole-thread circulation improves carrier self-confinement relative to the identical zero-thread-circulation control.
- **H-P:** active threading produces a more negative central-minus-shell pressure.
- **H-B:** the symmetric pressure law has a negative leading even quadratic coefficient in beta.
- **H-G:** the freely fitted far-field exponent is Newton-like *after reveal* and is stable under box/grid convergence.
- **H-GEAR:** triple-gear active threading improves a geometric phase-lock proxy; no preselected mechanical ratio is allowed.

Passing one does not imply another.

## Geometry qualification fixed before blinding

Default gates:

- source provenance must pass;
- maximum absolute carrier/thread Gauss-link estimate >= 0.75;
- hole clearance > `2.4 a`;
- exact complete-geometry initial nonlocal segment gap > `2.5 a`.

A failed geometry is excluded before candidate randomization.

## H-SC pair hierarchy

1. Full-horizon candidate beats a contact-stopped candidate.
2. If both stop, only longer survival may win; a small survival-time difference is a tie.
3. Only when both reach the full horizon are the primary metric log-ratios used.
4. Primary full-horizon metrics: initial relative-equilibrium residual, shape AUC, RPO residual, positive maximum real local modal growth.
5. Pair tie margin defaults to 2% in extended campaigns.
6. Inferential sign test is performed after one aggregate vote per carrier. Repeated beta/pitch/thread settings are not independent experimental units.

## H-P

For each carrier, take the median over its tested active conditions of

\[
\Delta p = (p_c-p_s)_{\rm active}-(p_c-p_s)_{\rm null}.
\]

Negative is favorable. Apply an exact one-sided sign test across nonzero carrier medians at alpha=0.05.

## H-B

Use symmetric beta pairs. Per carrier estimate the median even quadratic coefficient. `B<0` is favorable. Apply the exact one-sided sign test across carriers at alpha=0.05. The quartic polynomial fit is diagnostic and is not allowed to replace a failed symmetric-pair gate.

## H-G

The blind runner fits `p_A(r)-p_B(r)` and searches `nu` freely before sealing. Since A/B reversal changes amplitude sign but not exponent, this is the induced active-minus-null exponent without condition disclosure. Reveal includes only profiles above the preregistered minimum radial-fit R2 and not at the exponent-search boundary. Per carrier, take the median fitted exponent.

Post-seal target comparison:

- target `nu_N = 1`;
- alternative `nu_2 = 2`;
- default target tolerance `|nu-nu_N| <= 0.25`;
- carrier must be closer to target than alternative.

A gravity-closure survival verdict additionally requires a dedicated convergence campaign in which the carrier-median exponent span across the preregistered grid/box ladder is below the configured tolerance. A single-box campaign can at most support a pressure deficit; it cannot close H-G.

## Stability island scan

The stability-island run is **discovery only**. No p-value based on the best scanned point is confirmatory. A newly sealed fixed-setting campaign is required afterward.

## H-GEAR

No expected ratio is present in blind inputs or scoring. The code may search small `p,q` and report the best geometric phase relation after dynamics. This remains exploratory until a ratio selected from one campaign is fixed and tested in a new campaign.
