# Method

## 1. Matched geometry

For each topology shared by ideal and Fremlin sources, the preparation stage selects one canonical entry from each source, samples it densely, uniformly resamples arclength and canonicalizes rigid orientation and RMS radius. It then fixes a geometric phase anchor and traversal direction, eliminating source-file start-index/circulation-sign conventions as a numerical confound. The resulting anonymous curves are then resampled again at the blind-run resolution.

This prevents point density, global scale, translation and rotation from deciding the source comparison.

## 2. Relative-equilibrium residual

Given centerline velocity `v`, fit the least-squares rigid velocity

\[
\mathbf v_{\rm rigid}(\mathbf x)=\mathbf U+\boldsymbol\Omega\times(\mathbf x-\bar{\mathbf x}).
\]

The remaining tangential part is marker reparametrization and is also removed. The dimensionless initial residual is

\[
R_{\rm RE}=\frac{\|\mathbf v-\mathbf v_{\rm rigid}-\mathbf v_{\parallel}\|_{\rm RMS}}
{\|\mathbf v\|_{\rm RMS}}.
\]

A smaller value means the initial curve is closer to pure rigid translation/rotation under the tested vortex-filament dynamics.

## 3. Shape drift

At recorded times, the evolved curve is compared with its own initial curve after optimal cyclic marker shift and proper rigid `SE(3)` alignment. This removes trivial translation, rotation and material phase.

The normalized time integral of this RMS distance is `shape_auc`; the final value is `final_shape_distance`.

## 4. High-mode contamination

After uniform arclength sampling, a discrete curvature vector is Fourier transformed along the closed centerline. The fraction of curvature-spectrum power above the preregistered cutoff is reported. This is not used as a proxy for topology or ideality; it tests whether the same dynamics injects strong small-scale curvature structure.

## 5. Local restoring modes

A Bishop-frame transverse Fourier basis perturbs the centerline by `+eps/-eps`. Finite differences of the quotient shape velocity form a reduced Jacobian. `max_real_growth_positive` penalizes locally growing modes; the fraction of negative diagonal mode responses is retained as a secondary restoring diagnostic.

## 6. Recurrence

`rpo_residual` is the minimum nontrivial aligned distance back to the initial shape after a preregistered early-time exclusion. It is a recurrence proxy, not a full Newton-refined RPO or true monodromy calculation.

## 7. Contact

The package does not reconnect vortex lines. When the exact closest distance between non-adjacent finite centerline segments drops below the configured multiple of the core radius, integration stops and `contact_survival_deficit` penalizes that candidate. This directly enforces the no-reconnection research target instead of silently continuing through an unmodeled event.
