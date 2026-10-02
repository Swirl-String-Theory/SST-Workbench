# v0.3.0 preregistration: Kelvin threaded-hole gate

The following choices are fixed before active/null identity reveal.

## Primary blinded comparison

Lower is favorable for every primary cost:

```text
hole_robustness_cost
hole_geometry_collapse_cost
hole_class_instability_cost
hole_lagrangian_incoherence_cost
```

The anonymous pair winner is the sign of the median log-ratio of these costs, subject to the existing contact/full-horizon hierarchy.

## Basic preset thresholds

See `config/preset_kelvin_hole_basic.json` for exact machine-readable values. Key gates are:

\[
f_{\rm through}\ge0.50,
\qquad
f_{\rm resident}\ge0.72,
\qquad
f_{\rm side}\le0.35,
\]

\[
\frac{c_{\rm final}}{c_{\rm initial}}\ge0.70,
\qquad
f_{\rm perturb,robust}\ge0.66,
\qquad
f_{\mathrm{perturb,same}}\ge0.66.
\]

These are numerical classification thresholds, not fitted SST constants.


## Frozen streamline integration

The frozen topology gate uses arclength rather than physical time:

\[
\frac{d\mathbf x}{ds}=\frac{\mathbf u_{\rm rel}}{|\mathbf u_{\rm rel}|}.
\]

The basic preset fixes `hole_streamline_arclength_scale=8.0` and `hole_streamline_ds_fraction=0.025`; the extended preset uses a longer/finer path budget. These parameters affect connectivity resolution, not the finite carrier-evolution horizon.

## No target leakage

The blind phase is forbidden to read or use:

- carrier identity;
- family identity;
- active/null identity;
- sign or magnitude of the private \(\beta\) parameter;
- a desired Kelvin topology class;
- \(\alpha\), gravitational exponents or SST canon target values.

The Kelvin analytic values \(\sqrt{3}\) and \(2.087253791\ldots\) are used only by the separate pre-campaign numerical oracle. They never enter candidate ranking.

## Reveal inference

After SHA-256 seal verification, anonymous candidates are mapped to active/null identities. No new favorable metric is selected. The causal comparison uses the **anonymous multi-cost winner and median log-cost effect already written and sealed during the blind phase**. Repeated conditions are collapsed to one carrier-level vote before the exact one-sided sign test.

Existence is reported separately from causal attribution. A robust hole in both active and null arms establishes a dynamical transport structure within the tested model, but does not attribute it to central-thread circulation.

## Confirmatory interpretation

A causal supportive result requires a carrier-clustered sealed active advantage. A single visually compelling topology, a single optimized \(\beta\) condition, or a post-reveal single-metric advantage is insufficient.
