# S37B Mesh-Gauge Closure Diagnostic — v0.3.1

## 1. Motivation

In the v0.3.0 prospective run, four S35 core-robust trefoil realizations reached S37A and
zero passed.  Two failure patterns were observed:

1. low-rate segment feedback approached a mesh-quality stop for one source lineage;
2. another lineage remained score-stable while its final embedded curve changed more than
   the frozen S37A shape tolerance across mesh rates.

S37B distinguishes point-label/arclength drift from geometric centreline drift.

## 2. Frozen physical map

For a given candidate and resolution, all S37B arms share exactly the same

- initial arclength-normalized centreline;
- regularized Biot-Savart / finite-core physical RHS;
- global-volume core policy;
- RK4 integration plan `(steps, dt)`;
- physical final time;
- guard sampling stride.

Only the tangential numerical mesh velocity differs.

## 3. Mesh velocities

### 3.1 OFF control

`mesh_off` sets

\[
\mathbf{u}_{\mathrm{mesh}}=\mathbf{0}.
\]

### 3.2 Existing segment feedback

For segment lengths \(\ell_i\), mean \(\bar\ell\), and tangent \(\mathbf{t}_i\),

\[
\alpha_{i+1}-\alpha_i=-k(\ell_i-\bar\ell),
\qquad
\mathbf{u}_{\mathrm{mesh},i}=\alpha_i\mathbf{t}_i.
\]

The periodic compatibility condition holds because

\[
\sum_i (\ell_i-\bar\ell)=0.
\]

### 3.3 Independent arclength-target projection

Let \(\mathbf{x}_i^*\) be the uniform-arclength resampling target of the current polygon.
Only the tangent projection of its displacement is applied:

\[
\mathbf{u}_{\mathrm{mesh},i}
=
k\left[(\mathbf{x}_i^*-\mathbf{x}_i)\cdot\mathbf{t}_i\right]\mathbf{t}_i.
\]

Both controllers therefore add zero intended normal velocity to floating-point precision.
This does **not** imply exact gauge invariance of the discrete time-stepped polygon; S37B
is designed to measure that defect.

## 4. Displacement decomposition

After common cyclic and rigid alignment, define

\[
\delta\mathbf{x}_i=\mathbf{x}^{(B)}_i-\mathbf{x}^{(A)}_i.
\]

With the reference tangent \(\mathbf{t}_i\),

\[
\delta\mathbf{x}_{\parallel,i}
=(\delta\mathbf{x}_i\cdot\mathbf{t}_i)\mathbf{t}_i,
\]

\[
\delta\mathbf{x}_{\perp,i}
=\delta\mathbf{x}_i-\delta\mathbf{x}_{\parallel,i}.
\]

The reported RMS diagnostics are

\[
D_{\parallel}
=\sqrt{\frac1N\sum_i\|\delta\mathbf{x}_{\parallel,i}\|^2},
\qquad
D_{\perp}
=\sqrt{\frac1N\sum_i\|\delta\mathbf{x}_{\perp,i}\|^2}.
\]

Because different tangential flows change material labels, these raw-label quantities are
**diagnostic**, not a formal closest-normal distance between smooth curves.

## 5. Parameterization-invariant shape metric

The primary geometric metric is `D_shape`.  Each closed polygon is first uniformly
resampled by arclength, then cyclically and rigidly aligned.  The resulting RMS distance
suppresses pure point-density/label differences and is the same shape metric family used
by the existing S37A gate.

## 6. Resolution closure

For an arm error \(e_N=D_{\mathrm{shape}}(N)\) relative to mesh-OFF, S37B fits

\[
e_N\propto N^{-p}
\]

by a log-log slope.  Positive \(p\) indicates decreasing gauge dependence with resolution.
A `GAUGE_CLOSURE_SUPPORTED_DIAGNOSTIC_ONLY` label requires at least three resolution
levels and the configured minimum observed order.  This status still does not replace
S37A.

## 7. Frozen admission boundary

The key rule is

\[
\boxed{\text{S37B never promotes to S40.}}
\]

The original S37A result alone controls S40 eligibility.  Therefore the v0.3.0 observation
`0/4 S37A-qualified` cannot be repaired retroactively by S37B.

## 8. Post-hoc mode

`run_mesh_closure_from_v030.cmd` is provided only to diagnose the already-completed v0.3.0
anonymous geometries.  It re-hashes each public geometry against the old public manifest
and records the source evidence-file SHA-256 values.  It never opens the sealed identity
bundle.  Results are labeled `POSTHOC_DIAGNOSTIC_NOT_PREREGISTERED`.
