# SST Threaded-Hole Substrate Blind Falsifier v0.2.0

Blind C++/Python workbench for the hypothesis that a knotted high-circulation carrier can couple to a closed bundle of vortex tubes passing through its central hole, with two deliberately independent questions:

1. does the threaded substrate create a **self-confining / restoring stability island** for the carrier?;
2. does the same substrate create a reproducible **coarse-grained pressure deficit and far-field power law**?

A positive pressure result is not counted as a stability result, and neither is sufficient to establish gravity.

## Physical model

All components live in one incompressible inviscid filament model. The velocity field is the VortexLab-style regularized Biot-Savart + local-induction split. Each substrate thread is a **closed vortex loop**: a central straight/helical pass crosses the carrier hole and a distant return leg closes the line, avoiding vorticity endpoints.

For fixed-total-bundle coupling,

```text
beta = N_threads * Gamma_thread / Gamma_core
Gamma_thread = beta * Gamma_core / N_threads
```

For density studies, `thread_coupling_mode=per_thread_beta` instead keeps `Gamma_thread/Gamma_core` fixed while `N_threads` varies.

## Carrier strata

- Torus: analytic `T(2,3)`, `T(2,5)`, `T(2,7)`, `T(2,9)`.
- Twist: source-qualified Fremlin `4_1`, `5_2`, `6_1`, `7_2`; the thread axis is found geometrically/topologically rather than assumed to be the PCA z-axis.
- Triple gear: analytic `T(3,3)` three-component link. Each carrier component is individually an unknot; the three are pairwise linked and share one central threaded passage.

A carrier can still be excluded after source qualification. v0.2 requires exact initial finite-segment clearance greater than `2.5 a` by default. Under the standard v0.2 geometry the current `TWIST_6_1` thread construction fails this clearance gate and is excluded rather than being allowed to generate a tau=0 contact run.

## v0.2 methodological gates

### G0 — pre-blind qualification

- source provenance acceptable;
- central-hole clearance acceptable;
- Gauss-link probe indicates actual threading;
- exact minimum nonlocal segment distance > `min_initial_gap_core * a`.

### G1 — hierarchical contact / self-confinement

A contact-stopped trajectory is never scored with ordinary truncated AUC/RPO/Floquet metrics.

```text
PASS_FULL_HORIZON vs FAIL_CONTACT -> full-horizon wins contact gate
FAIL_CONTACT vs FAIL_CONTACT      -> only survival time is compared
PASS vs PASS                      -> preregistered dynamical metrics are compared
```

Primary full-horizon metrics are lower-is-better:

- initial relative-equilibrium residual;
- shape AUC;
- RPO recurrence residual;
- positive part of maximum real local modal-growth eigenvalue.

### G2 — carrier-cluster inference

Repeated beta/pitch/density scans of one knot are **not independent samples**. Reveal first takes a within-carrier aggregate, then performs the exact sign test across carriers. Condition-level counts remain descriptive only.

### G3 — pressure law

The dedicated pressure campaign scans beta symmetrically and post-seal fits

```text
Delta p(beta) = A beta + B beta^2 + C beta^3 + D beta^4
```

with a separate even/odd decomposition. The candidate thread-self pressure mechanism predicts a negative even quadratic coefficient `B`, but the fit is not forced to have that sign.

### G4 — free far-field exponent

Before reveal, the blind runner forms the anonymous pair-difference profile `p_A(r)-p_B(r)` and fits it to the following free power law. Reversing A/B changes only the coefficient sign, not the exponent, so this is equivalent to fitting the induced active-minus-null profile without reading condition identity:

```text
p(r) = p0 + K / r^nu
```

where `nu` is searched freely over a preregistered interval. No Newton exponent is supplied to the field solve or exponent search. Only after the result tree is sealed does reveal compare the fitted carrier-level exponent with `nu=1` and the `nu=2` alternative.

### G5 — far-field convergence

A Newton-like claim cannot pass from one finite periodic FFT pressure box. `run_all_far_field.cmd` repeats the pressure solve at multiple `(grid_n, box_half)` settings and requires the fitted exponent to remain stable.

### G6 — stability-island discovery

`run_all_stability_islands.cmd` scans beta, thread count and helix turns per carrier. The best point is explicitly labelled **DISCOVERY ONLY**. It must be confirmed in a future fresh fixed-parameter campaign; no minimum selected from the same scan receives a confirmatory p-value.

### G7 — triple-gear phase proxy

For the `T(3,3)` proxy, v0.2 tracks geometric cyclic phase of each unknot component and of each central thread after quotienting global carrier rigid motion. It discovers the best small rational relation `p:q` between mean carrier and thread phase rates. No mechanical gear ratio is supplied to the blind code.

This is a geometric phase proxy, not a material-marker proof of mechanical teeth.

## Ready-to-run Windows scripts

Fast smoke/basic:

```cmd
run_all.cmd
```

General dynamics + pressure:

```cmd
run_all_extended.cmd
```

Fine beta pressure law without expensive time evolution:

```cmd
run_all_pressure_law.cmd
```

Multi-grid / multi-box free-exponent convergence:

```cmd
run_all_far_field.cmd
```

Long carrier-specific stability-island discovery:

```cmd
run_all_stability_islands.cmd
```

Triple gear + geometric phase locking:

```cmd
run_all_triple_gear.cmd
```

Circulation similarity (`Gamma_core = 0.5, 1, 2` at fixed dimensionless coupling):

```cmd
run_all_similarity.cmd
```

Density / helix campaign using fixed circulation per thread:

```cmd
run_all_density_helix.cmd
```

Confirmatory core bundle (extended + pressure-law + far-field + triple-gear):

```cmd
run_all_full.cmd
```

The long stability-island discovery is deliberately not included automatically in `run_all_full.cmd` because it is a large exploratory scan.

## Main outputs

Every campaign writes:

```text
outputs/<campaign>/campaign/blind_catalog/
outputs/<campaign>/campaign/private/
outputs/<campaign>/blind/
outputs/<campaign>/reveal/
```

Useful reveal files:

- `REVEAL_SUMMARY.json`
- `CONCLUSIONS.md`
- `revealed_pairs.csv`
- `pressure_law.csv`
- `stability_islands_discovery.csv`
- `triple_gear_phase_lock.csv`

The blind result tree, public anonymous geometry/catalog, code, config and private-key commitment are SHA-256 sealed before reveal.

## Interpretation guard

A result of the form

```text
threading -> lower central pressure
```

does **not** establish

```text
threading -> stable particle
```

or

```text
pressure deficit -> Newtonian gravity.
```

v0.2 requires these gates independently. In particular a gravity closure requires: carrier-clustered pressure support, a free exponent consistent with the preregistered Newton target after reveal, and a stable far-field exponent across the convergence ladder.
