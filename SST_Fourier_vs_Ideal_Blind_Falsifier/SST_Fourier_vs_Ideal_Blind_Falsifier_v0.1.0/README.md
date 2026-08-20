# SST Fourier-vs-Ideal Blind Dynamical Falsifier v0.1.0

Purpose: test the observed VortexLab claim that a smooth Fremlin `.fseries` seed is dynamically closer to a coherent inviscid vortex state than the corresponding Brian Gilbert tight/ideal seed, with a secondary optional control against KnotPlot/RidgeRunner relaxed coordinates.

## Primary hypothesis

For matched knot topology and identical nondimensional circulation/core/scale/resolution, the `.fseries` candidate should exhibit less non-rigid dynamical departure under the same VortexLab-style filament equation.

The claim is **not** scored from appearance, ropelength, source metadata, or SST target constants. It is scored from anonymous paired dynamics and revealed only after SHA-256 sealing.

## One-command runs

From the package folder on Windows:

```cmd
run_all.cmd
```

This is the torus-focused blind campaign. It runs install -> native build attempt -> source preparation -> blind dynamics -> automatic seal -> post-seal reveal.

For every common knot ID:

```cmd
run_all_extended.cmd
```

For the original source comparison plus an additional `.fseries` vs `KnotPlot\knots\final` control when a topology can be matched:

```cmd
run_all_relaxed_control.cmd
```

## Expected SST Workbench paths

Defaults in `config\paths.cmd`:

```text
..\..\KnotPlot\Knots_FourierSeries
..\..\KnotPlot\knots\final
```

For the ideal source the resolver checks, in order, explicit environment overrides and common Workbench locations such as:

```text
..\..\SSTcore\resources\ideal.txt
..\..\SSTcore\resources\ideal_knots_data.js
..\..\VortexLab\ideal.txt
..\..\VortexLab\ideal_knots_data.js
..\..\KnotPlot\ideal.txt
```

If your ideal source is elsewhere:

```cmd
set SST_FVI_IDEAL=C:\path\to\ideal.txt
run_all.cmd
```

or

```cmd
set SST_FVI_IDEAL_JS=C:\path\to\ideal_knots_data.js
run_all.cmd
```

Source discovery only:

```cmd
run_05_find_sources.cmd
```

## Blind architecture

Preparation is the only stage allowed to know source identity and topology. It creates:

```text
blind_catalog\
  pairs_public.csv
  manifest_public.json
  geometry\CAND_*.npz

private\
  candidate_key.csv
  pair_key.csv
  source_discovery.json
```

`pairs_public.csv` contains anonymous A/B pairings only. The blind runner never reads `private\`. The public manifest contains a SHA-256 commitment to the private identity key before any dynamics are run.

Each blind candidate is independently normalized to:

- RMS radius = 1;
- a deterministic geometric phase anchor and traversal direction;
- uniform arclength sampling;
- identical point count per component;
- `Gamma = 1` per component;
- identical finite-core ratio and core model.

No damping, mutual friction, VortexLab auto-relax, target ropelength, SST particle mapping, or source label enters the ODE.

## VortexLab-style dynamics

The native kernel follows the same structural split used by VortexLab: a local-induction term plus a nonlocal Biot-Savart segment sum. For one component,

\[
\mathbf u_i = \frac{\Gamma}{4\pi}
\left[\ln\!\left(\frac{2\sqrt{\ell_-\ell_+}}{e^{\Delta}a}\right)+c_0\right]
\mathbf s'_i\times\mathbf s''_i
+\frac{\Gamma}{4\pi}\sum_{j\notin\{i-1,i\}}
\frac{d\boldsymbol\ell_j\times\mathbf r_{ij}}{|\mathbf r_{ij}|^3}.
\]

Defaults use the VortexLab GP-core convention `Delta = 0.615` and measured discretization constant `c0 = 0.1395`. Integration is RK4 with a Kelvin-wave CFL estimate and arclength redistribution as marker-gauge control.

## Preregistered primary observables

Lower is better:

1. `contact_survival_deficit`;
2. `initial_relative_equilibrium_residual` after quotienting translation, rotation and tangential marker velocity;
3. `shape_auc` after optimal cyclic + SE(3) alignment;
4. `final_shape_distance`;
5. `peak_high_mode_fraction` of curvature-spectrum power;
6. `rpo_residual`, the best nontrivial recurrence to the initial shape;
7. `max_real_growth_positive` from a local transverse Fourier/Bishop-mode Jacobian.

For each anonymous pair, the median log-ratio across those metrics determines A/B/tie. Source identity is still unknown at this stage.

After sealing, reveal converts the anonymous score into

\[
D=\operatorname{median}_m\ln\frac{x_{\mathrm{fseries},m}+\epsilon}
{x_{\mathrm{reference},m}+\epsilon}.
\]

`D < 0` favors `.fseries`; `D > 0` favors the reference. Aggregate evidence uses a preregistered one-sided exact sign test at `alpha = 0.05` plus a minimum median effect of 10%. Thresholds are never adjusted during reveal.

## Torus stratum

The torus-focused preparation uses standard knot-table IDs when present:

```text
3_1, 5_1, 7_1, 8_19, 9_1, 10_124
```

The report keeps the torus stratum separate from the all-knot aggregate. With the currently validated Fremlin archive plus VortexLab/Gilbert catalog, the matched torus set is `3_1`, `5_1`, `7_1`; 3/3 wins would still give only a one-sided exact sign-test `p=0.125`. The package therefore reports the torus effect separately and never weakens the threshold. The current all-knot intersection contains 13 matched knot IDs and is the stronger aggregate campaign.

## Output

Blind:

```text
outputs\blind_*\
  blind_summary.json
  blind_pair_results.csv
  cases\CAND_*.json
  cases\PAIR_*_pair.json
  SEALED_MANIFEST.json
  BLIND_RESULT_SHA256.txt
```

Post-seal:

```text
outputs\blind_*_revealed\
  revealed_pair_results.csv
  REVEAL_SUMMARY.json
  CONCLUSIONS.md
```

## Interpretation

A `.fseries` win does **not** prove an SST particle or a stable Euler solution. It establishes the narrower claim that, for this fixed filament model and preregistered diagnostics, the Fourier seed is closer to coherent inviscid evolution than its matched reference. The strongest winning candidates can then be passed to the separate Self-Confinement / Restoring-Force Balance falsifier for pressure-Poisson, Hamiltonian Hessian, Floquet and nonlinear closure gates.
