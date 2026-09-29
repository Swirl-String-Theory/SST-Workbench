# A047 v0.4.0 preregistration

## Primary question

For the anonymously selected follow-up subset of the E010/PKLSA-v0.3.1 trefoil population, is the v0.3.0 short-time increase of `||omega||_infinity` a **seed-resolved, spatially and temporally converged Euler vortex-stretching mechanism**, and does any surviving trajectory show resolution-stable finite-time BKM-compatible scaling that outperforms nonsingular growth models?

## Frozen parent selection

The follow-up population is selected exclusively from v0.3.0 `BLIND/summary.json`. Source-family, carrier ID, variant ID, source path and SST constants are unavailable to the selector. The selector freezes and hashes its anonymous result before the v0.3.0 reveal map is read.

Default maximum: 8 geometries. One representative from every anonymous parent independence group is mandatory; anomaly slots then target best inverse-omega fit, earliest future `t_star`, and greatest amplification. No manual named-carrier override is part of the default protocol.

## Upstream E010 gate

After blind selection is frozen, every parent-selected carrier must still belong to the current default-admitted E010-v0.3.1 `3_1` population. Source bytes are reloaded and both `raw_sha256` and `PKLSA-GEOMETRY-SHA256-v1` are rechecked exactly as in v0.3.0.

## S10 seed/core gate

A case is seed-certified at resolution `N` only when all configured conditions pass:

\[
\sigma/\Delta x \ge n_{\sigma,\min},
\quad 3\sigma\kappa_{\max}\le C_\kappa,
\quad d_{\rm periodic}/\sigma\ge C_{\rm box},
\]

and the dealiased outer spectral-energy fraction is below its threshold. BASIC freezes `(n_sigma_min,C_kappa,C_box)=(4,0.5,3)` and spectral tail `<=0.08`.

Seed failure is not a PDE failure. It classifies subsequent dynamics as screen-only unless a config explicitly requests exploratory continuation.

## S20 spatial gate

Convergence is same-geometry only. BASIC uses `N=32,48,64`, fixed physical/dimensionless window `T=0.24` and `dt` proportional to `N^-2`. For `omega_growth` and sampled BKM integral, the finest-level relative change must be `<=5%` and the three-level order estimator must be at least 1.0 or hit an explicit numerical floor.

`certified_spatial_pass` additionally requires the finest seed/core gate.

## S22 temporal gate

Extended mode uses fixed `N=64` with `dt,dt/2,dt/4 = 0.001,0.0005,0.00025`. Each configured observable must either achieve `p_observed >= 2.8` or be classified at the relative numerical floor.

## S30 numerical validity

Every dynamical replay requires its configured energy-drift and divergence gates. Failure blocks all downstream interpretation for that replay.

## S40 mechanism gate

For long-window survivors, v0.4.0 evaluates:

1. velocity-gradient decomposition `M=S-(1/2) epsilon dot omega`;
2. incompressible deformation `det(F) ~ 1`;
3. Cauchy vorticity transport `omega ~ F omega_0`;
4. stretching closure `log(|omega|/|omega_0|) ~ integral alpha dt`, `alpha=xi^T S xi`.

Default hard tolerances are `1e-10`, `0.08`, `0.20`, and `0.20`, respectively. The sample-time `F_tt + H F` residual is diagnostic only in this version.

## S50 finite-time model gate

Across 35%, 45%, and 55% trailing windows, finite-time power-law growth must beat both exponential and nonsingular algebraic models by `Delta AICc >=10`, have `gamma>=0.9`, and maintain relative `t_star` spread `<=0.15`.

A good `R^2` for `1/omega` by itself cannot create an escalation candidate.

## S60 robustness gate

Only pre-robustness model candidates enter the optional core/mesh sweep. Extended mode varies centerline resampling and core sigma; default allowed spread in `omega_growth` is 12%. The sweep is a sensitivity gate, not an excuse to optimize parameters after seeing a desired result.

## Blindness

BLIND outputs contain parent anonymous geometry/group IDs, selection reasons, numerical settings, convergence/seed/mechanism/model diagnostics and anonymous case IDs. Carrier/source identities and local source paths remain in REVEALED provenance.

## Prohibited inference

No tested outcome establishes global Euler regularity. `NO_*_CANDIDATE` means only that this finite family, initialization and numerical protocol did not satisfy the preregistered escalation chain.
