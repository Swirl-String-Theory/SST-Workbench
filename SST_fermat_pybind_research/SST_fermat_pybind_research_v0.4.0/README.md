# SST Fermat pybind research v0.4.0

Standalone Python + C++17/pybind11 research harness. It does **not** import, modify, or patch SSTcore.

This release turns the v0.3 softening scan into a candidate-certification pipeline for the fixed four-knot matrix

\[
0_1,\qquad 3_1,\qquad 4_1,\qquad 5_2.
\]

The bundled centerlines are reconstructed from the uploaded `ideal_favorites.txt` Fourier database. The package remains **Research Track** software: it certifies numerical stationary structures and convergence diagnostics, not a physical electron model or a global photon sphere.

## Why v0.4.0 is a major release

v0.3 counted sampled local minima of

\[
R_F(\rho;s,\theta)
=
\frac{\rho}{\sqrt{1-\lVert\boldsymbol\beta\rVert^2}}.
\]

v0.4 instead solves the stationary equation directly:

\[
\boxed{
G(\rho;s,\theta)
=
1-\lVert\boldsymbol\beta\rVert^2
+
\rho\,\boldsymbol\beta\cdot\partial_\rho\boldsymbol\beta
=0.
}
\]

Since

\[
\frac{\partial R_F}{\partial\rho}
=
\frac{G}{\left(1-\lVert\boldsymbol\beta\rVert^2\right)^{3/2}},
\]

a sign change from \(G<0\) to \(G>0\) identifies a local radial minimum.

## New in v0.4.0

1. **Analytic Biot--Savart field Jacobian** in C++ and Python:

   \[
   J_{ij}=\frac{\partial\beta_i}{\partial x_j}.
   \]

2. **Bracketed stationary-root solver** using a coarse radial discovery grid followed by batched bisection.
3. **Candidate convergence certification** across at least three centerline resolutions \(N,2N,4N\).
4. **Bifurcation atlas** across \(\epsilon/r_c\), with branch IDs and onset/loss tracking.
5. **Independent knot-scale sweep** through `scale_over_rc`.
6. **Approximate reach diagnostic** from curvature and subsampled doubly-critical chord candidates.
7. **Symmetry/covariance audit** for translation, proper rotation, orientation reversal, cyclic reindexing, and mirror reflection.
8. **Orbit-seed catalog** generated from converged local minima; no global orbit claim is made.
9. Native/Python parity gates for both the field and its analytic Jacobian.
10. Existing v0.3 profile, softening, and resolution tools remain available as regression diagnostics.

## Kernel scope

The full three-dimensional knot field still uses the regularized midpoint Rosenhead kernel

\[
\boldsymbol\beta(\mathbf x)
=
\frac{\beta_0}{2}
\sum_i
\frac{
\Delta\boldsymbol\ell_i\times
(\mathbf x-\mathbf x_{i+1/2})
}{
\left(\lVert\mathbf x-\mathbf x_{i+1/2}\rVert^2+\epsilon^2\right)^{3/2}
}.
\]

Its analytic spatial derivative is computed from

\[
\frac{\partial}{\partial x_j}
\left(
\frac{r_k}{Q^{3/2}}
\right)
=
\frac{\delta_{kj}}{Q^{3/2}}
-
\frac{3r_kr_j}{Q^{5/2}},
\qquad
Q=\lVert\mathbf r\rVert^2+\epsilon^2.
\]

Rankine and Lamb--Oseen remain one-dimensional comparison profiles only; they are not silently substituted into the full three-dimensional knot solver.

## Epistemic status labels

A root can be labelled:

```text
CERTIFIED_LOCAL_MINIMUM_NUMERICAL
LOCAL_MAXIMUM
DEGENERATE_STATIONARY_POINT
GLOBAL_CAUSTIC_REGIME
NOT_CONVERGED
```

`CERTIFIED_LOCAL_MINIMUM_NUMERICAL` means that a stationary radial minimum was solved numerically in one transported normal plane. It does **not** mean that a closed Fermat geodesic exists in the full non-axisymmetric metric.

Every result preserves:

```json
"global_closed_orbit_certified": false,
"qsm_certified": false
```

The reach value in v0.4 is explicitly an approximate diagnostic, not a rigorous Ridgerunner/reach certificate.

## Build the native module

From the project root in an activated virtual environment:

```bat
python -m pip install -r requirements.txt
python -m fermat_ext.build_ext_if_needed --force --strict
```

v0.4 changes the native binding by adding `biot_savart_batch_with_jacobian`; rebuild the `.pyd` even when v0.3 was already compiled.

## 1. Full audit

```bat
python run_all_checks.py --out-dir audit_out_native --no-auto-build --require-native
```

The native release gate includes:

\[
\begin{aligned}
&\text{field parity}<10^{-12},\\
&\text{Jacobian parity}<10^{-10},\\
&\text{analytic Jacobian finite-difference check}<10^{-7},\\
&\text{external radial benchmark error}<10^{-10}.
\end{aligned}
\]

## 2. Candidate atlas for all four knots

A first native run:

```bat
python run_candidate_atlas.py --epsilon 0.0019 --centerline-points 8192 --stations 8 --angles 16 --bracket-samples 96 --no-auto-build --require-native --out-dir candidate_atlas_0019
```

For a higher angular/station resolution:

```bat
python run_candidate_atlas.py --epsilon 0.0019 --centerline-points 16384 --stations 32 --angles 32 --bracket-samples 128 --no-auto-build --require-native --out-dir candidate_atlas_0019_high
```

Primary outputs:

```text
candidate_atlas.json
candidate_atlas.csv
0_1.json
3_1.json
4_1.json
5_2.json
```

## 3. Candidate convergence certification

Start with:

```bat
python run_candidate_convergence.py --epsilon 0.0019 --point-counts 4096 8192 16384 --stations 8 --angles 16 --bracket-samples 96 --no-auto-build --require-native --out-dir convergence_0019
```

For the more demanding \(4_1\) and \(5_2\) cases:

```bat
python run_candidate_convergence.py --knots 4_1 5_2 --epsilon 0.0019 --point-counts 8192 16384 32768 --stations 8 --angles 16 --no-auto-build --require-native --out-dir convergence_0019_high
```

Weak certification requires the candidate branch to occur at at least three resolutions and satisfy

\[
E_\rho<10^{-3},\qquad
E_{R_F}<10^{-3},\qquad
E_\beta<10^{-3}.
\]

Strong certification uses \(10^{-4}\).

## 4. Bifurcation atlas

The primary v0.4 scan window is

\[
0.00180\leq\epsilon/r_c\leq0.00210.
\]

```bat
python run_bifurcation_atlas.py --epsilon-start 0.00180 --epsilon-stop 0.00210 --epsilon-step 0.000025 --centerline-points 8192 --stations 8 --angles 16 --no-auto-build --require-native --out-dir bifurcation_atlas
```

This tracks branches by knot, station, angular sector, and nearest \(\rho_\star\). The reported threshold shift is diagnostic until the branch itself passes the convergence run.

## 5. Independent knot-scale sweep

The Fourier source normalization \(D=1\) is not a physical identification with \(r_c\). Test the scale dependence explicitly:

```bat
python run_scale_sweep.py --scales 0.5 1.0 2.0 4.0 --epsilon 0.0019 --centerline-points 8192 --stations 8 --angles 16 --no-auto-build --require-native --out-dir scale_sweep_0019
```

The relevant local/non-local geometry changes with

\[
\frac{D_K}{\epsilon}
=
\frac{\texttt{scale\_over\_rc}}{\epsilon/r_c}.
\]

## 6. Symmetry audit

```bat
python run_symmetry_audit.py --epsilon 0.0019 --centerline-points 4096 --no-auto-build --require-native --out-dir symmetry_audit
```

The scalar quantities \(\lVert\boldsymbol\beta\rVert^2\), \(S\), \(R_F\), and \(G\) must remain invariant under rigid transformations and centerline orientation reversal. The vector and Jacobian are checked using their proper vector/pseudovector transformation laws.

## 7. Legacy v0.3 diagnostics

The following remain supported:

```text
run_profile.py
run_profile_matrix.py
run_sweep.py
run_knot_scan.py
run_knot_matrix.py
run_softening_matrix.py
run_resolution_ladder.py
```

They are useful for reproducing v0.3 outputs, but the new v0.4 root solver should be used for candidate claims.

## Performance notes

The native Jacobian kernel performs substantially more arithmetic than the field-only kernel. Candidate discovery batches all radial probes, and bisection refines all active brackets together. Nevertheless, high-resolution runs with \(N=32768\), many stations, and many angular sectors can require significant RAM and runtime.

Recommended sequence:

1. audit;
2. candidate atlas at \(N=8192\);
3. convergence only for knots/softenings where roots were found;
4. bifurcation atlas;
5. scale and symmetry audits.

## What v0.4 can and cannot conclude

v0.4 can distinguish among:

```text
candidate disappears under refinement
candidate is a universal core-profile feature
candidate remains knot-geometry dependent after convergence
```

v0.4 does not yet integrate or shoot a complete closed Fermat orbit. That belongs to a later geodesic/monodromy release after the local branches survive certification.