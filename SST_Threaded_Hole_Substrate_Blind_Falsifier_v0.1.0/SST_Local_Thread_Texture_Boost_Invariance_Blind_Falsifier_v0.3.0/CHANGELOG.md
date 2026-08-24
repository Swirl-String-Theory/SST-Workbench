# Changelog

## v0.3.0 — numerical certification + finite-source/local-texture upgrade

This release was built **from the uploaded v0.2.0 package itself**.  The upload already contained explicit closed vortex filaments, remote return flux, fixed core radii, shared hidden orientations and nonlinear multi-step evolution.  Those are therefore retained, not claimed as new v0.3 features.

### 1. RK2 -> classical RK4

**v0.2.0:** midpoint RK2.

**v0.3.0:** four-stage RK4, with the knot self-field and source-thread field recomputed at every stage.

Why: the bridge responses are small enough that time-discretization error should not be allowed to masquerade as a topology/thread response.  v0.3 also adds an independent time-refinement certification gate at the highest spatial resolution.

### 2. Midpoint segment approximation -> exact regularized straight-segment integral

v0.2 evaluated each polygon edge by a midpoint approximation to the regularized Biot--Savart line integral.  v0.3 analytically integrates the same Rosenhead-regularized kernel along every straight polygon edge.

Why: increasing bead count should test the geometry, not simultaneously remove a first-order segment quadrature error.  The new kernel is implemented independently in Python and C++.

### 3. Constant final time + ds^2 subcycling

Every case now freezes a single

\[
T_{\rm final}
\]

before execution.  An outer RK4 step is subdivided when the committed bound

\[
\Delta t_{\max}=C_{\Delta s^2}\frac{\Delta s^2}{|\Gamma|}
\]

is smaller than the requested outer step.  Subcycling never changes \(T_{\rm final}\).

Why: a spatial ladder must not accidentally compare different physical integration durations.  The extended/high-resolution runner reports spatial and temporal convergence separately.

### 4. Arclength reparameterization

After a complete outer RK4 step, each closed knot/link component can be redistributed uniformly in polygonal arclength while keeping the same bead count.

Why: v0.2 could accumulate bead clustering during multi-step evolution.  Reparameterization is applied only after full RK4 steps; no restoring force is added to the right-hand side.

### 5. Explicit core-clearance audit

v0.3 measures the minimum knot-thread centerline clearance and normalizes it by

\[
a_{\rm knot}+a_{\rm thread}.
\]

If the cores overlap, structural covariance tests may still PASS, but dynamical bridge claims are classified `INDETERMINATE` rather than treated as evidence.

Why: v0.2 could evolve a knot while a background thread passed through its finite core, without flagging that interpretation problem.

### 6. Return-flux gate strengthened

In addition to evolved-shape and local-field convergence, v0.3 verifies that the **local outgoing thread legs are numerically identical** when only the remote closure distance is changed.

Why: the locality test should change the remote return path and nothing else.

### 7. Thread-density mechanism split

v0.2 represented a density gradient by varying circulation weights across a fixed lattice.  v0.3 separates two cases:

1. circulation-weight gradient at fixed thread positions;
2. positional/number-density gradient at fixed per-thread circulation.

Both are normalized to matched total circulation.

Why: "more vortex threads per area" is not mathematically identical to "the same threads with larger circulation".  The falsifier should not silently identify those mechanisms.

### 8. Finite-source curvature -> local parallel limit

v0.3 adds a closed radial-source bundle with a hidden finite source center and a committed source-distance ladder.  It tests whether

\[
D/R_g\rightarrow\infty
\]

converges monotonically to the locally parallel bundle used for Earth-/Sun-sized sources.

Why: v0.2 assumed the large-source-radius limit directly.  v0.3 now falsifies that approximation instead of merely stating it.

### 9. Separate certification gates

`run_extended.py` now produces:

- `C1_spatial_fixed_core_convergence`;
- `C2_temporal_RK4_convergence`.

The core radii and \(T_{\rm final}\) must remain fixed across the spatial ladder.  The temporal gate reruns the highest \(N\) with a refined time step.

### 10. Prior-release holdout runner

Added:

```cmd
run_holdout_certification.cmd
run_all_holdout.cmd
```

Default holdout search strings:

```text
link_0.3.1
torus_6.21
```

These were the previously identified difficult convergence cases.  The runner copies only matched inputs into a committed holdout subset and applies the v0.3 spatial + temporal certification ladder.

### 11. Hidden transverse lattice phase

v0.2 centered the hexagonal thread lattice on the knot centroid, which implicitly placed one bundle thread at a privileged transverse phase.  v0.3 commits a hidden transverse lattice offset for each orientation, uses the same normalized phase set for every topology, and carries the same phase into the return-flux and finite-source controls.

Why: orientation alone is not the complete relative geometry between a discrete thread bundle and a knot.  The transverse phase must also be sampled rather than hand-picked.

## v0.2.0 — retained baseline

The uploaded v0.2.0 already introduced explicit closed vortex filaments, local parallel source bundles, remote return paths, midpoint RK2 evolution, fixed core radii, shared hidden orientation sets, primary/secondary bundles and a return-flux locality gate.  v0.3.0 preserves that physical architecture while strengthening its numerical and interpretive falsification gates.
