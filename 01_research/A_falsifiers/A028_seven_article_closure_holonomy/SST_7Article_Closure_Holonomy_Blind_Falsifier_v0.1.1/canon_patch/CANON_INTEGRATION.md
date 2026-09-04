# Canon v0.8.35 integration decision

The compiled `SST_CANON-v0.8.35.pdf` is accessible in the connected source set and confirms the existing pressure-envelope and analogue-metric sectors.  The exact editable `SST_CANON-v0.8.35.tex` and `SST_CANON-v0.8.35-research-track.tex` source files were not available to this execution environment.  Therefore this release deliberately provides **standalone insertion blocks**, not a falsely claimed line-perfect Git patch.

## Main-canon placement

Use `SST_CANON-v0.8.35-seven-article-closure-addendum.tex` in the consistency/closure methodology area.  Two existing v0.8.35 anchors make the integration particularly natural:

- `K.7 Spherical Pressure Envelopes`: extend the local radial pressure discussion with the general three-dimensional pressure-Poisson identity and Green/boundary guard.
- `S.36.10 Analogue-metric bridge`: append the principal-symbol rule and the distinction between effective probe geometry and substrate geometry.

The remaining topology-layer, representation-invariance, and kinematics-versus-dynamics rules fit best in the canon consistency/provenance methodology section rather than inside a phenomenology block.

Only these items are suitable for main-canon promotion now:

1. exact incompressible pressure-Poisson identity + Bernoulli scope guard;
2. topology-layer non-equivalence guard;
3. representation-invariance/on-shell rule;
4. effective-metric principal-symbol guard;
5. kinematics-vs-dynamics inference guard.

## Research track

Use `SST_CANON-v0.8.35-research-track-seven-article-closure-addendum.tex` for the detailed spectral, phase, even/odd, finite-core, holonomy, and cosmographic falsifier programme.  The existing research-track pressure-envelope section should retain Bernoulli only with its declared stationary assumptions and point to the general Poisson closure for arbitrary evolving 3-D knots.

## Do not canonize

Do not copy as SST laws:

- Ising CFT ratios `2:4:6:8`;
- acoustic Hopf invariant `Q_H=l_tor l_pol`;
- MoS2 nonlinear phase law `3 Delta theta`;
- magnetic-vortex Ellis throat `a_q`;
- acoustic transport dilation `rho`;
- logarithmic HL `q(z)`.

Those are source-system formulas used as methodological precedents only.

## v0.8.35 protocol-review compatibility

The existing v0.8.35 protocol review identifies coarse compound epistemic tags as a release issue and recommends statement-level separation of orthodox input, exact deduction, ansatz, calibration and bridge/theorem target.  This addendum follows that discipline: exact continuum identities are separated from SST-specific theorem targets and research ansätze.

## To obtain a line-perfect `.diff`

Place the two exact v0.8.35 `.tex` sources next to this package and insert the two addendum blocks at the anchors above.  A unified diff can then be generated mechanically and checked with `git apply --check`.  Until those source bytes are available, claiming an applicable line-number patch would be misleading.
