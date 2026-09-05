# Scientific protocol — v0.2.0

## Primary hypotheses

**H1 — Dynamic seed existence.** At least one preregistered trefoil geometry has early free dynamics dominated by coherent symmetry motion rather than destructive intrinsic deformation.

**H1b — Local discoverability.** A blinded, bounded neighborhood around top H1 seeds can identify a reproducible local high-quality region without revealing provenance.

**H2s — Spatial robustness.** Seed ranking/metrics persist across the fixed spatial ladder.

**H2t — Temporal robustness.** The same observables are converged under fixed-N timestep refinement.

**H2c — Core robustness.** Seed quality is not a narrow artifact of one regularized core fraction.

**H2g — Mesh-gauge robustness.** Parameterization-invariant geometry is insensitive, within frozen tolerances, to low/nominal/high purely tangential mesh-control strength.

**H3 — Orbital recurrence.** A numerically certified seed exhibits at least one nontrivial symmetry-reduced near return in a preregistered observation window.

**H4 — Projected Floquet stability.** An H3 candidate has projected nontrivial Floquet spectral radius below the frozen threshold.

**H5 — Material-core mechanism specificity.** On an H4 candidate, a measured stretch-to-acceleration delay improves held-out prediction for the material-core model and beats the matched fixed-core null by the frozen margin.

## Anti-overfitting / anti-pseudoreplication rules

1. Source identities and deformation parameters are sealed through S20-S60.
2. Source geometries are deduplicated after normalized cyclic/rigid alignment before candidate generation.
3. Candidate scheduling is source-stratified; one source may not consume the entire discovery budget before other accepted sources are represented.
4. Score weights and all parameter ranges are frozen in config before S10.
5. S25 may refine only anonymous S20 parents inside frozen local ranges.
6. POD effective rank and QHP-like low-dimensional structure are diagnostic-only; neither may boost seed score.
7. S30 and S32 independently certify spatial and temporal numerics.
8. S35 uses a frozen core-radius ladder and reports a champion cluster. A unique winner needs the preregistered margin.
9. S37 certifies invariance under a purely tangential numerical mesh gauge before a seed enters S40.
10. No later stage may nominate a seed that failed an upstream qualification stage.
11. S50 may not turn insufficient S40 numerical coverage into a physics FAIL.
12. S60 may not run unless an S50 candidate exists.
13. S60 discovers delay only from simulation data and tests it on holdout data; no target phase or user-supplied return time enters the dynamics.
14. A material-only predictive improvement is not enough: material must beat the fixed-core null by `causal_min_material_advantage_over_fixed`.
15. `dt ~ ds^2` is preserved; no silent timestep coarsening is permitted.
16. Numerical PASS is never relabelled as SST confirmation.

## Geometry / rolling observables

Each snapshot is re-expressed on uniform normalized arclength, cyclically aligned, rigidly Kabsch-aligned and then normal-projected for shape comparisons.

Initial rolling is estimated from

\[
\mathbf u_\perp(s)=\mathbf V+\boldsymbol\Omega\times(\mathbf X-\mathbf X_c)+\mathbf r(s).
\]

A strong candidate has a small normal residual `r`, low symmetry-reduced shape-drift AUC, limited high-k excitation, acceptable contact separation and acceptable mesh quality. A true static relative equilibrium is not penalized merely for having low rigid velocity.

## S32 temporal gate

For each selected candidate at fixed N, run timestep factors

\[
f_0,\quad f_0/2,\quad f_0/4.
\]

Let `E01` and `E12` be parameterization-invariant final-shape discrepancies. If both are below the absolute floor/tolerance, the case is certified as floor-limited. Otherwise the observed order is

\[
p=\log_2(E_{01}/E_{12})
\]

and must exceed the frozen minimum.

## S37 mesh-gauge gate

The geometry-only controller is strictly tangential:

\[
\alpha_{i+1}-\alpha_i=-k(\ell_i-\bar\ell),\qquad
\mathbf u_{\rm mesh}=\alpha_i\hat{\mathbf t}_i.
\]

Its RMS is capped relative to physical Biot-Savart RMS velocity. Candidate trajectories are replayed with the frozen gauge multipliers. Passing requires completion to the gauge horizon plus bounded pairwise final-shape distance and bounded score/AUC spread.

The mesh gauge is a numerical parameterization device, not an SST force.

## S40 coverage and epistemic result

For each long trajectory, S40 always records a complete status schema: completion, stop reason, actual/target horizon, best return/time, local ds-CV and gap at return, and maximum mesh/physical RMS ratio.

A near-return can enter S50 only if it occurs after `rpo_min_observation_time` and satisfies all local numerical gates. A later mesh stop does not erase a previously certified return, but it does reduce global long-horizon coverage.

S40 may emit a hard `FAIL_NO_NEAR_RPO_WITH_VALID_COVERAGE` only when the preregistered minimum number/fraction reaches the observation window and the required full-horizon coverage is achieved. Otherwise the result is explicitly `INDETERMINATE_*`.

## S50 projected Floquet scope

The monodromy is evaluated on a preregistered finite Fourier-normal perturbation basis. `floquet_rho_max` applies only to this projected subspace. It is not a theorem about the full `3N` filament tangent space or a volumetric 3-D Euler core.

## S60 causal scope

The proposed mechanism is

\[
\text{mode-projected material stretch}(t)
\longrightarrow
\tau_{\rm measured}
\longrightarrow
\ddot a(t+\tau).
\]

The same analysis is run on a fixed-core null. A mechanism candidate requires both an absolute held-out material improvement and a material-minus-fixed advantage. The measured loop phase is reported only after the lag is determined.

## Recommended scientific use

- BASIC: pipeline + first source-stratified search.
- EXTENDED: primary scientific campaign after BASIC integrity inspection.
- PRODUCTION: only after configs/ranges/thresholds are frozen and package/config SHA256 values are archived before reveal.
