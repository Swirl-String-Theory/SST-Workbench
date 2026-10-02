# Preregistration — SST Phase-Feedback Delay Knot Stability Falsifier v0.2.0

**Status:** prospective confirmatory design, frozen before any v0.2.0 confirmatory result is inspected.

## Why v0.2.0 exists

v0.1.7 revealed two design defects: pseudoreplication (41 source files collapsed to 10 unique geometries) and a secondary absolute-growth closure whose scale/sign made its non-negative gain collapse to zero. v0.2.0 is a new test, not a reinterpretation of v0.1.7.

The 10 canonical-64 geometry hashes observed in v0.1.7 are frozen in `reference/v0.1.7_seen_canonical64_sha256.json`. In **confirmatory** mode they are excluded before blind IDs are assigned. Therefore re-running v0.1.7 geometries can only be a retrospective audit, never a v0.2 confirmatory result.

## Dataset identity and anti-pseudoreplication gate

Every input centerline is uniformly resampled to 128 points for exact analysis identity hashing. Exact identity hashes are grouped **before statistical analysis**. A separate 64-point hash is used only for comparison with the frozen v0.1.7 historical registry. One blind candidate is created per unique identity geometry. Source filenames and multiplicities remain in the private reveal key.

Confirmatory eligibility requires at least 8 **novel unique** canonical geometries after excluding the frozen v0.1.7 registry. No source-file multiplicity is ever treated as an independent replicate.

## Independent loop-delay measurement

The modal eigenfrequency `omega_m` is still obtained from the fixed regularized Biot–Savart linearization. However loop delay is no longer derived from `d omega / d k`.

For each preregistered carrier mode a localized helical Kelvin packet is constructed in the closed Bishop frame and evolved with the same **unforced** C++ RK4/Biot–Savart dynamics. After Kabsch removal of rigid motion, the perturbation-energy centroid

\[
C(t)=\frac{\sum_j w_j(t)e^{i2\pi j/N}}{\sum_jw_j(t)},\qquad
w_j=\|\delta X_j\|^2
\]

is unwrapped around the loop. A linear centroid fit gives

\[
v_{g,m}^{packet}=\frac{L}{2\pi}\frac{d\arg C}{dt},\qquad
\tau_m=\frac{L}{|v_{g,m}^{packet}|}.
\]

Packet modes must satisfy all frozen quality thresholds in the selected config (`R^2`, angular span, centroid coherence and velocity floor). A candidate requires at least the configured number of valid packet modes, and at least 80% of blind unique candidates must be valid; otherwise the result is **INCONCLUSIVE**, not a hypothesis failure.

The phase score is

\[
\Theta_m=(\omega_m\tau_m)\bmod 2\pi,\qquad D_m=1-\cos\Theta_m,
\]

with candidate score `D = median(D_m)` over valid preregistered packet modes.

## Independent nonlinear stability measurement

The nonlinear measurement does not use packet-delay validity to choose perturbations. It uses the fixed mode list in the config, evolves paired unforced trajectories, Kabsch-aligns them, and fits exponential shape departure. Growth is made dimensionless using

\[
t_{char}=\frac{L^2}{|\Gamma|},\qquad \Sigma=\sigma_{obs}t_{char}.
\]

The candidate response is the median dimensionless growth over the fixed nonlinear mode list.


## Primary endpoint versus robustness run

`configs/basic.json` is the **single primary confirmatory endpoint**. `configs/extended.json` is preregistered as a higher-resolution **robustness-only** analysis. The extended result may corroborate or expose resolution sensitivity, but it may not rescue a primary basic FAIL and is not a second opportunity to claim confirmatory PASS.

## Gate 1 — rank prediction

With at least 8 valid novel unique candidates, require

\[
\rho_S(D,\Sigma)\le -0.5,\qquad p\le0.05.
\]

No gain parameter is fitted for this gate.

## Gate 2 — hash-defined untouched holdout

Unique candidates are assigned by SHA-256 of `PFD-v0.2-split:` plus identity geometry hash. If that creates fewer than the frozen minimum counts on either side, canonical hashes are sorted and alternated deterministically.

On training only, compare:

- baseline: `Sigma_hat = mean(Sigma_train)`;
- delay model: `Sigma_hat = a + b D`, with **b <= 0**.

The delay model must have `b < 0` and reduce untouched holdout RMSE by at least 10% versus the constant baseline.

No per-knot, per-mode, family-specific or post-reveal fitting is allowed.

## Orthogonal preparation audit

After reveal, multiplicities of source files per unique geometry are reported separately. This audit does **not** increase statistical N and cannot convert a phase-delay FAIL into PASS. Its fixed descriptive classification is:

- unique fraction <= 0.50: `STRONG_ENDPOINT_COLLAPSE`;
- unique fraction >= 0.80: `PREPARATION_SENSITIVE`;
- otherwise: `MIXED_ENDPOINT_SENSITIVITY`.

## Decision rule

- **PASS:** dataset/packet quality gates pass, Gate 1 passes, and Gate 2 passes.
- **FAIL:** quality gates pass but either confirmatory physics gate fails.
- **INCONCLUSIVE:** too few novel unique candidates, pseudoreplication invariant violation, insufficient packet transport quality, or insufficient holdout sizes.

`legacy_audit` mode can exercise the machinery on previously seen v0.1.7 geometries, but its `claim_status` is always `RETROSPECTIVE_ONLY`.

A confirmatory PASS supports this specific packet-delay ranking mechanism within the regularized filament model. It does not establish a finite-core Euler/SST derivation. A FAIL falsifies this preregistered v0.2.0 closure, not every possible memory kernel.
