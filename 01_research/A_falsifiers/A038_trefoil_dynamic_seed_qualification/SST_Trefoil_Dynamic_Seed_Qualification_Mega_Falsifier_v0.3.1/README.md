# SST Trefoil Dynamic Seed Qualification Mega Falsifier v0.3.1

## Purpose

v0.3.1 is a targeted numerical diagnostic release.  The v0.3.0 prospective campaign found
four trefoil seeds that passed spatial-resolution, temporal and finite-core robustness
checks, but **0/4 passed S37 mesh-gauge certification**.  v0.3.1 asks a narrower question:

> Does changing a purely tangential mesh controller merely relabel points along the same
> embedded filament, or does it materially change the physical centreline produced by the
> discrete solver?

The old mesh-gauge gate is retained as **S37A**.  The new layer is **S37B** and is diagnostic
only.  S37B cannot authorize S40, RPO/Floquet, Phase B or a physics claim.

## Pinned dependency

Scientific atlas runs require:

```text
sst-knot-library/0.2.5
```

Default repository-relative location:

```text
Knot_Library\SST_Knot_Library\SST_Knot_Library_v0.2.5
```

or set `SST_KNOT_LIBRARY_HOME` explicitly.

## S37B arms

The default prospective diagnostic compares, at each resolution:

```text
mesh_off
segment_feedback @ 2.4
segment_feedback @ 4.0
segment_feedback @ 5.6
target_projection @ 4.0
```

All arms use the **same frozen RK4 step count, dt, target physical time and guard stride**
for a given candidate/resolution.  `mesh_off` still uses the same global-volume finite-core
physical RHS; only the numerical mesh velocity is zeroed.

The prospective one-click profile uses:

```text
N = 64, 96, 128
T = 1.2
```

`production.json` adds `N = 192` and runs all three rates for both tangential controllers.

## Diagnostics

After rigid/cyclic alignment, the raw point-label displacement is decomposed into

```text
D_parallel : RMS component along the reference tangent
D_perp     : RMS component normal to the reference tangent
```

A second metric, `D_shape`, first resamples both closed curves by arclength and then
rigid/cyclic aligns them.  `D_shape` is therefore the primary approximate
parameterization-invariant embedded-curve diagnostic.

S37B reports:

- mesh-off versus each controller arm;
- within-controller mesh-rate sensitivity;
- segment-feedback versus target-projection controller sensitivity at matched rates;
- final and trajectory-maximum `D_shape`, `D_parallel`, `D_perp`;
- ds-CV, contact margin and mesh/physical speed ratio;
- empirical convergence order from `D_shape(N)` where enough resolution levels exist.

See `docs/MESH_GAUGE_CLOSURE_v0.3.1.md`.

## Interpretation statuses

S37B may report:

```text
GEOMETRIC_CENTERLINE_COUPLED_TO_MESH_GAUGE
NUMERICALLY_UNRESOLVED_AT_FINEST_RESOLUTION
GAUGE_CLOSURE_SUPPORTED_DIAGNOSTIC_ONLY
INDETERMINATE_INSUFFICIENT_RESOLUTION_LEVELS
INDETERMINATE_MESH_GAUGE_CLOSURE
```

Even the strongest status contains the words **DIAGNOSTIC_ONLY**.  S37A remains the only
mesh admission gate for S40.

## One-click prospective campaign

```bat
run_all_atlas.cmd C:\workspace\projects\SST-Workbench
```

The chain is:

```text
setup -> native C++/pybind build -> selftests
      -> pinned Knot Library verification
      -> prospective atlas freeze + KnotRecord binding
      -> S20 -> S30 -> S32 -> S35
      -> S37A frozen mesh-gauge certification
      -> S37B mesh-gauge closure diagnostic
      -> gated S40 -> S50 -> S60 -> Phase B
      -> BLIND archive
      -> reveal verification
      -> REVEALED archive
```

Default output root:

```text
./SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.1-outputs/
```

The shareable archives are written one directory above the project:

```text
SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.1-outputs_BLIND.zip
SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.1-outputs_REVEALED.zip
```

The blind ZIP excludes `sealed/`, `*_sealed_private/`, blind keys and private identity/source
audit material.

## Fast diagnostic on the completed v0.3.0 campaign

To test the new S37B code without re-running S20-S35:

```bat
run_mesh_closure_from_v030.cmd C:\path\to\v0.3.0\scientific_campaign_v030
```

This reads only the old **public** manifest, S35/S37 summaries and committed anonymous
geometries.  Its output is explicitly marked:

```text
POSTHOC_DIAGNOSTIC_NOT_PREREGISTERED
```

It cannot retroactively certify S37A or authorize S40.

## Scientific non-claims

This package does not establish SST, full 3D Euler stability, a stable trefoil RPO,
publication-grade Floquet stability or a causal finite-core feedback mechanism.  It is a
numerical-closure diagnostic inside the regularized vortex-filament surrogate.
