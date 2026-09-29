# SST Euler Regularity / BKM Singularity Gate v0.4.0 (A047)

**Resolution-Certified Lagrangian Vortex-Stretching & BKM Mechanism Gate.**

v0.4.0 is the staged follow-up to the successful v0.3.0 E010/PKLSA-v0.3.1 population screen. The parent run had 116/116 numerically valid source-native trefoil evolutions, no short-window BKM candidate, but widespread finite-window vorticity amplification. v0.4.0 asks whether that amplification is a converged Euler mechanism or a core/grid/initialization effect, and only then tests finite-time BKM-compatible scaling.

## Scientific change from v0.3.0

v0.3.0 was a broad anomaly screen. v0.4.0 is a **gated funnel**:

```text
v0.3.0 BLIND population output (116 geometries)
        |
        | S00 blind follow-up selection
        v
   <= 8 geometries
        |
        | S10 seed/core admissibility + S20 spatial convergence
        v
   spatial survivors
        |
        | S22 temporal convergence (extended config)
        v
   temporal survivors
        |
        | S30 long Euler + S40 Lagrangian mechanism closure
        | S50 singular/nonsingular model competition
        v
   pre-robustness candidates
        |
        | S60 core/mesh robustness (extended config)
        v
   escalation candidate or negative/indeterminate result
```

A later stage can never rescue a failed upstream certification gate.

## S00 — parent-blind selection

Selection is frozen from **v0.3.0 BLIND observables only**, before the v0.3.0 reveal map is opened. Default policy selects at most eight geometries:

1. one max-growth representative from every anonymous v0.3.0 independence group;
2. global best inverse-omega fit;
3. earliest positive future `t_star`;
4. global maximum growth;
5. deterministic median/low-growth controls only when criteria overlap.

Only after `S00_parent_blind_selection.json` and its SHA-256 are written is the reveal map used to recover E010 carrier IDs. This avoids source-family/variant-name driven follow-up selection.

The provided snapshot of the uploaded v0.3.0 result reproduces `116 -> 8` with five anonymous independence groups. Runtime selection is recomputed from the user's actual parent output and is not hard-coded.

## S10 — seed/core admissibility

For every `(geometry, N)` v0.4.0 records separately:

\[
n_\sigma=\frac{\sigma}{\Delta x},\qquad
3\sigma\kappa_{\max},\qquad
\frac{d_{\rm periodic}}{\sigma},
\]

plus the fraction of retained spectral energy in the outer part of the dealiased cube.

Default certification thresholds are:

\[
n_\sigma\ge4,\qquad
3\sigma\kappa_{\max}\le0.5,\qquad
\frac{d_{\rm periodic}}{\sigma}\ge3,
\]

and spectral-tail fraction `<= 0.08`.

The audit also estimates the `N` required by the grid-core gate and the joint grid/slender-core requirement. A clean energy/divergence history does **not** override an under-resolved seed.

## S20/S22 — convergence

Spatial convergence is assessed only among different `N` replays of the **same geometry**. The BASIC profile uses `N=32,48,64` with `dt ~ N^-2`. Default observables are vorticity amplification and the sampled BKM integral.

Temporal convergence uses `dt, dt/2, dt/4` at fixed `N` and requires observed order `p >= 2.8`, unless the observable is explicitly classified at the numerical floor.

Different E010 carriers and independence groups are never pooled as resolution replications.

## S30/S40 — long dynamics and mechanism closure

The extended profile uses a fixed long window (`T=0.9` by default) only for upstream survivors. At sample times it follows a material tracer and deformation gradient

\[
\dot X=u(X,t),\qquad \dot F=M F,\qquad M=\nabla u.
\]

It evaluates:

\[
M=S-\frac12\epsilon\cdot\omega,
\qquad
\frac{D|\omega|}{Dt}=\alpha|\omega|,
\quad \alpha=\xi^T S\xi,
\]

and the Cauchy relation

\[
\omega(X(a,t),t)\approx F(a,t)\omega_0(a),\qquad \det F\approx1.
\]

The pressure Hessian `H = grad grad p` is also evaluated. `F_tt = -H F` is reported as a lower-order sample-time diagnostic; it is not a hard gate in v0.4.0.

## S50 — model competition

The old single `1/omega_max` linear fit is retained as a diagnostic, but no longer acts alone. Across 35%, 45% and 55% trailing windows v0.4.0 compares

\[
\omega_{\max}=A(t_*-t)^{-\gamma}
\]

against exponential and nonsingular algebraic growth. Default finite-time escalation requires:

- `Delta AICc >= 10` versus the best nonsingular model in every window;
- `gamma >= 0.9` in every window;
- relative `t_star` spread `<= 0.15` across fit windows.

## Final verdict vocabulary

Possible outputs include:

- `SCREEN_ONLY_NO_CERTIFIED_ESCALATION`
- `CONVERGED_TRANSIENT_AMPLIFICATION_SEED_UNCERTIFIED`
- `SPATIALLY_CERTIFIED_AMPLIFICATION`
- `TEMPORALLY_CONVERGED_AMPLIFICATION_NO_CERTIFIED_BKM_MODEL`
- `BKM_MODEL_CANDIDATE_PENDING_ROBUSTNESS`
- `ESCALATE_ROBUST_BKM_SCALING_CANDIDATE`

There is deliberately **no `EULER_REGULARITY_PASS` verdict**.

## Run

Place `A047-v0.4.0` beside the existing v0.3.0 directory. By default the runner looks for the parent output at:

```text
../SST_Euler_Regularity_BKM_Singularity_Gate_v0.3.0/
   SST_Euler_Regularity_BKM_Singularity_Gate_v0.3.0-outputs/
```

Then:

```cmd
run_all.cmd C:\workspace\projects\SST-Workbench
```

This uses `config\v040_basic.json`: S00 + S10/S20 only.

Extended pipeline:

```cmd
run_all_extended.cmd C:\workspace\projects\SST-Workbench
```

Software/integration smoke:

```cmd
run_all_smoke.cmd C:\workspace\projects\SST-Workbench
```

An explicit parent output can be supplied as the third argument:

```cmd
run_all.cmd C:\workspace\projects\SST-Workbench config\v040_basic.json C:\path\to\SST_Euler_Regularity_BKM_Singularity_Gate_v0.3.0-outputs
```

See `docs/PREREGISTRATION.md`, `docs/CROSS_CHAT_RATIONALE.md`, and `VALIDATION.md`.
