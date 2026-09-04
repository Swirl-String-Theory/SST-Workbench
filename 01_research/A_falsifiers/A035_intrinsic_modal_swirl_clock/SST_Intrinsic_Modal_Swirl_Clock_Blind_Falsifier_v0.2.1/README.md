# SST Intrinsic Modal Swirl-Clock Blind Falsifier v0.2.1

Numerical-certification release for the intrinsic modal swirl-clock programme.

## Purpose

The primary Stage-A question is deliberately narrower than the final SST mechanism claim:

\[
\boxed{\text{Does a relaxed closed vortex centerline possess a numerically certifiable recurrent intrinsic shape mode?}}
\]

Only after such a mode survives long-horizon, mesh-quality and mesh-gauge tests does Stage B ask whether material vortex stretching and a measured delay provide a causal/core-specific mechanism.

Default seed dataset:

```text
..\..\KnotPlot\knots\final
```

The package uses the existing Ridgerunner/KnotPlot-relaxed centerlines. New KnotPlot seeds are not required for this discovery/certification stage.

## Why v0.2.1

The v0.2.0 `T=24` run improved long-horizon integration substantially but only 3/49 carriers satisfied the strict `ds_cv <= 0.20` certification gate. Therefore a dataset-wide negative verdict was not justified. v0.2.1 fixes the verdict logic and removes the remaining dependence of POD coordinates on the numerical bead parameterization.

## Run

```bat
run_all.cmd
```

or explicitly:

```bat
run_all.cmd ..\..\KnotPlot\knots\final
```

The BASIC chain is now:

```text
1  prepare blind -eps / 0 / +eps arms
2  nominal Stage A, T=24
3  parameterization-invariant early-POD + provisional recurrence analysis
4  low mesh-gauge replay on provisional candidates only
5  high mesh-gauge replay on provisional candidates only
6  mesh-gauge candidate certification
7  material-core Stage B on certified candidates only
8  fixed-core Stage B null
9  causal/core-specificity analysis
```

Long runs print anonymous candidate progress, e.g.

```text
[stage_a 031/147] start candidate=... carrier=... arm=0
[stage_a 031/147] done t=24/24 ds_cv=0.143 stop=COMPLETED mesh/phys=0.82
```

## Stage A dynamics

Regularized finite-core Biot-Savart remains the physical centerline evolution. Stage A uses a geometry-compatible global core volume law

\[
a^2(t)L(t)=a_0^2L_0,
\]

because its numerical mesh is allowed to slide tangentially and therefore bead indices are not interpreted as material parcels.

### Segment-feedback tangential mesh gauge

Let segment lengths be \(\ell_i\) and \(\bar\ell\) their mean. v0.2.1 constructs a periodic scalar tangential speed \(\alpha_i\) from

\[
\alpha_{i+1}-\alpha_i=-\kappa\left(\ell_i-\bar\ell\right),
\]

then applies only

\[
\mathbf u_{\rm mesh,i}=\alpha_i\hat{\mathbf t}_i.
\]

Hence the explicit numerical controller has no normal component in the continuum geometry description. Its RMS magnitude is also capped relative to the physical Biot-Savart RMS velocity and reported for audit.

The certification gate remains strict:

\[
\boxed{ds_{\rm CV,max}\le0.20}.
\]

No post-hoc relaxation of this threshold is performed.

## Parameterization-invariant modal analysis

Before any Stage-A POD or frozen-mode projection, every saved snapshot is converted to a geometry-only canonical representation:

\[
\mathbf X_i(t)
\rightarrow
\mathbf X(s_j,t),\qquad s_j=j/N,
\]

using uniform closed-curve arclength resampling. The arbitrary cyclic origin along the closed curve is aligned, rigid translation/rotation are removed, and only normal displacement is retained.

This prevents the POD basis from interpreting the deliberately introduced tangential bead redistribution as a physical shape mode.

## Modal channels

Three matched arms are generated for each anonymous carrier:

\[
-\epsilon,\quad0,\quad+\epsilon.
\]

Two independent channels are analyzed:

**Natural carrier motion**

\[
\delta\mathbf X_{\rm natural}(t)=\mathbf X_0(t)-\mathbf X_0(0).
\]

**Odd linear response**

\[
\delta\mathbf X_{\rm odd}(t)=
\frac{\mathbf X_+(t)-\mathbf X_-(t)}{2\epsilon}.
\]

Even probe contamination is separately measured from

\[
\frac{\mathbf X_++\mathbf X_-}{2}-\mathbf X_0.
\]

## Frozen discovery window

The spatial POD basis is learned only from the absolute early interval

\[
\boxed{0\le t\le1.2}
\]

and is then frozen. Increasing the total horizon does not increase the fitting interval.

BASIC Stage A:

\[
T_A=24,\qquad N_{\rm cycles}\ge4.
\]

EXTENDED:

\[
T_A=36,\qquad N_{\rm cycles}\ge6.
\]

## Recurrence gates

For a modal coordinate \(a_k(t)\), v0.2.1 requires more than a spectral peak. It tests the phase-space state

\[
\mathbf z_k=(a_k,\dot a_k)
\]

for returns at approximately

\[
T,2T,3T,4T,
\]

plus period stationarity, amplitude stationarity, low cycle-center drift, minimum modal discovery energy, minimum holdout amplitude, spectral concentration and harmonic consistency.

## Coverage-aware falsification

A negative dataset-wide result is allowed only when the numerical experiment has adequate coverage.

BASIC/EXTENDED defaults require:

\[
\frac{N_{\rm valid}}{N_{\rm total}}\ge0.80,
\qquad N_{\rm valid}\ge20,
\]

and every predeclared high-information carrier must be valid.

If not, the correct result is

```text
INDETERMINATE_STAGE_A_INSUFFICIENT_VALID_COVERAGE
```

rather than a global clock falsification.

The three predeclared certification-priority source patterns are the prior high-information cases `knot_6.3_final`, `link_4.2.1_final`, and `link_9.2.20_final`. Their identities remain private during scoring.

## Mesh-gauge certification

A provisional Stage-A recurrence is **not yet a PASS**. Only that carrier is replayed with mesh redistribution gains

\[
0.6\kappa_0,\qquad1.4\kappa_0.
\]

The nominal frozen spatial mode must remain recurrent in both gauges. Period, multi-return closure and amplitude must agree within predefined spreads. A surviving candidate is promoted to

```text
analysis\stage_a_candidates.json
```

and the Stage-A gate becomes

```text
PASS_STAGE_A_RECURRENT_SHAPE_CLOCK_MESH_GAUGE_CERTIFIED
```

## Stage B

Stage B never uses tangential remeshing. It restores material segment labels and compares

\[
a_i^2\ell_i=\text{const}
\]

against fixed core radius. The Stage-A mode is frozen and reused; Stage B cannot choose a new favorable mode.

It tests mode-projected material stretching against delayed modal acceleration, a zero-lag null, phase-scrambled timing nulls and material-vs-fixed specificity.

Possible final outcomes include:

```text
PASS_CANDIDATE_INTRINSIC_SWIRL_CLOCK_MECHANISM
PASS_STAGE_A_RECURRENCE__FAIL_OR_INDETERMINATE_STAGE_B_CAUSALITY
FAIL_STAGE_A_NO_RECURRENT_SHAPE_CLOCK
INDETERMINATE_STAGE_A_INSUFFICIENT_VALID_COVERAGE
```

## Output files

Key BASIC outputs:

```text
outputs\basic\analysis\blind_stage_a_summary.json
outputs\basic\analysis\blind_stage_a_carrier_summary.csv
outputs\basic\analysis\blind_stage_a_modal_results.csv
outputs\basic\analysis\stage_a_candidates_provisional.json
outputs\basic\analysis\blind_stage_a_gauge_results.csv
outputs\basic\analysis\blind_stage_a_gauge_summary.json
outputs\basic\analysis\stage_a_candidates.json
outputs\basic\analysis\blind_stage_b_results.csv
outputs\basic\analysis\blind_summary.json
```

Do not reveal identities before reviewing the blind outputs. Afterwards:

```bat
run_reveal.cmd outputs\basic
```

## Focus and resolution runs

```bat
run_focus_6p3.cmd
run_focus_link_4p2p1.cmd
run_focus_link_9p2p20.cmd
```

Each focus run requires 1/1 valid carrier for a negative verdict.

The resolution ladder:

```bat
run_resolution.cmd
```

uses the predeclared trio at

\[
N=64,96,128
\]

with the same `T=24`, performs mesh-gauge certification at each resolution, and compares only certified anonymous carrier/channel recurrences.

## Numerical safeguards

- RK4.
- fixed physical final time.
- `dt_factor` with \(\Delta t\propto\Delta s^2\).
- hard failure if the configured step cap would require timestep enlargement.
- no hidden timestep coarsening.
- C++17/pybind11/OpenMP regularized Biot-Savart backend.
- Windows/MSVC source uses `py::ssize_t`, never unqualified global `ssize_t`.

## Interpretation

A Stage-A PASS is evidence for a recurrent shape mode only within this regularized finite-core filament model. It does not by itself establish the proposed SST clock mechanism. A Stage-B PASS adds evidence for the specific stretch/delay/core mechanism, but still does not substitute for a volumetric 3-D Euler/pressure-Poisson test.
