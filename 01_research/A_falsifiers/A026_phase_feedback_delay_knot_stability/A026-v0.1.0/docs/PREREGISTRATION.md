# Preregistration — Phase Feedback Delay Knot Stability Falsifier v0.1.1

## Hypothesis under test

For a closed vortex-knot candidate, a self-returning phase/shape mode has a loop delay

\[
\tau_m = \frac{L}{|v_{g,m}|},\qquad v_{g,m}=\frac{d\omega_m}{dk},\qquad k_m=\frac{2\pi m}{L}.
\]

The preregistered positive-gain delayed-self-feedback closure gives the weak-feedback correction

\[
\delta\sigma_m \simeq K_m\,[\cos(\Theta_m)-1],\qquad \Theta_m=\omega_m\tau_m.
\]

Therefore the dimensionless phase score

\[
D_m=1-\cos\Theta_m\in[0,2]
\]

must rank candidates toward *lower* observed perturbation growth if this mechanism contributes materially to stability.

## No per-knot fitting

- `tau_m` is derived from the modal dispersion of the same regularized Biot--Savart operator.
- `omega_m` is an eigenfrequency of the same operator.
- The primary rank gate has **no gain parameter**.
- A secondary predictive gate may fit exactly one non-negative global dimensionless gain `kappa` on the hash-defined calibration half and must improve RMSE on the untouched blind holdout half.
- Per-knot, per-mode, or post-reveal gain fitting is prohibited.

## Primary gate

For at least 8 blind candidates:

1. Compute each candidate's median valid `D_m` over the fixed mode range.
2. Independently measure nonlinear paired-trajectory growth under the same unforced regularized Biot--Savart dynamics.
3. Require Spearman `rho <= -0.5` and `p <= 0.05`.

## Holdout gate

Use

\[
\widehat\sigma = \sigma_0 + \kappa z,\qquad
z=\operatorname{median}_m\{\omega_m[\cos(\Theta_m)-1]\},\quad \kappa\ge0.
\]

Fit `kappa` only on the hash-defined calibration subset. On holdout, delayed prediction must reduce RMSE by at least 10% versus `sigma_0` alone.

## Decision

- **PASS**: both primary rank and holdout gates pass.
- **FAIL**: enough candidates exist but either confirmatory gate fails.
- **INCONCLUSIVE**: fewer than 8 valid candidates or insufficient propagating modes.

A PASS supports this specific finite-delay closure within the regularized filament model. It does not establish an SST finite-core Euler derivation. A FAIL falsifies the tested closure/parameterization, not every possible memory kernel.
