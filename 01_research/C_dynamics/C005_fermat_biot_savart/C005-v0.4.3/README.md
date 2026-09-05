# SST Fermat pybind research v0.4.3

Standalone Python + C++17/pybind11 research harness. It does **not** import, modify, or patch SSTcore.

This release turns the v0.3 softening scan into a candidate-certification pipeline for the fixed four-knot matrix

\[
0_1,\qquad 3_1,\qquad 4_1,\qquad 5_2.
\]

The bundled centerlines are reconstructed from the uploaded `ideal_favorites.txt` Fourier database. The package remains **Research Track** software: it resolves numerical stationary structures and separately certifies convergence-qualified branches; it does not establish a physical electron model or a global photon sphere.

## v0.4.3 patch scope

v0.4.3 is a **reporting and audit-semantics release** built on the clock-safe v0.4.2 root solver. It does not change the Rosenhead field operator, the analytic Jacobian, or the stationary equation

\[
G(\rho;s,\theta)
=
1-\lVert\boldsymbol\beta\rVert^2
+
\rho\,\boldsymbol\beta\cdot\partial_\rho\boldsymbol\beta
=0.
\]

The release closes two ambiguities found in the successful v0.4.2 campaign.

## New in v0.4.3

1. **Clock-domain components are explicit.** Each sampled normal ray now reports:

   ```text
   valid_clock_ray_count
   fully_clock_valid_ray_count
   clock_boundary_bracket_count
   real_clock_component_count_total
   rays_with_disconnected_clock_domain
   clock_domain_splits
   ```

   A ray with an inner and outer real-clock interval is no longer summarized as unsplit. Clock-boundary brackets remain excluded from the stationary-root list.

2. **Candidate fractions have unambiguous denominators.** The output distinguishes

   \[
   P_{\rm valid},\qquad P_{\rm all},\qquad P_{\rm fully\ valid},
   \]

   through `candidate_surface_fraction_valid_clock_rays`, `candidate_surface_fraction_all_rays`, and `candidate_surface_fraction_fully_clock_valid_rays`. In particular,

   \[
   0\le P_{\rm all}\le1.
   \]

3. **Bifurcation thresholds are censored or bracketed, never guessed.** The misleading `epsilon_loss_sampled` wording is replaced by:

   ```text
   epsilon_first_present_sample
   epsilon_last_present_sample
   onset_left_censored
   loss_right_censored
   epsilon_onset_bracket_over_rc
   epsilon_loss_bracket_over_rc
   ```

   A sampled present/absent transition is labelled `BRACKETED_SAMPLED_THRESHOLD_NOT_CONTINUATION_CERTIFIED`.

4. **Regression coverage was extended.** The audit now verifies the split clock domain at \(\epsilon/r_c=0.0010\), six clock-boundary brackets for the three-ray control scan, and the distinction between any-valid and fully-valid rays.

5. The v0.4.2 scientific guards are unchanged:

   ```json
   "global_closed_orbit_certified": false,
   "qsm_certified": false
   ```

## Core v0.4 capabilities retained

- analytic Biot--Savart field Jacobians in C++ and Python;
- batched bracket discovery and stationary-root refinement;
- three-level candidate convergence reports;
- softening bifurcation branch tracking;
- independent ideal-knot scale sweeps;
- approximate curvature/DCSD reach diagnostics;
- rigid-motion, orientation, reindexing, and mirror covariance audits;
- orbit-seed output with the global-orbit and QSM guards preserved.

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
RESOLVED_LOCAL_MINIMUM
LOCAL_MAXIMUM
DEGENERATE_STATIONARY_POINT
GLOBAL_CAUSTIC_REGIME
NOT_CONVERGED
```

`RESOLVED_LOCAL_MINIMUM` means that a stationary radial minimum was solved numerically in one transported normal plane. It does **not** mean that a closed Fermat geodesic exists in the full non-axisymmetric metric.

Every result preserves:

```json
"global_closed_orbit_certified": false,
"qsm_certified": false
```

The reach value in v0.4.3 is explicitly an approximate diagnostic, not a rigorous Ridgerunner/reach certificate.

## Build the native module

From the project root in an activated virtual environment:

```bat
python -m pip install -r requirements.txt
python -m fermat_ext.build_ext_if_needed --force --strict
```

The native API includes `biot_savart_batch_with_jacobian`; rebuild the `.pyd` when upgrading from v0.3 or an older v0.4 development build.


## One-command full campaign

On Windows, double-click:

```text
START_V043_FULL_CAMPAIGN.bat
```

Equivalent command:

```bat
python run_full_campaign.py ^
  --preset full ^
  --require-native ^
  --resume ^
  --out-root v0.4.3_campaign_output ^
  --archive SST_fermat_pybind_research_v0.4.3_results.zip
```

The full sequence is:

```text
native build
audit_out_native
candidate_atlas_0019
candidate_atlas_0019_high
convergence_0019
convergence_0019_high (3_1, 4_1, 5_2)
bifurcation_atlas (adaptive, min N=32768)
scale_sweep_0019 (adaptive resolution)
symmetry_audit
combined ZIP + SHA-256
```

The BAT file uses `--resume`. After an interruption, run the same BAT again; completed steps with valid success markers are skipped. The full bifurcation and scale runs are intentionally expensive. Use `START_V043_SMOKE_CHECK.bat` first to verify the local compiler and pybind module.

## 1. Full audit

```bat
python run_all_checks.py ^
  --out-dir audit_out_native ^
  --no-auto-build ^
  --require-native
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
python run_candidate_atlas.py ^
  --epsilon 0.0019 ^
  --resolution-mode adaptive ^
  --target-ds-over-epsilon 1.0 ^
  --min-centerline-points 4096 ^
  --max-centerline-points 65536 ^
  --stations 8 ^
  --angles 16 ^
  --bracket-samples 96 ^
  --no-auto-build ^
  --require-native ^
  --out-dir candidate_atlas_0019
```

For a higher angular/station resolution:

```bat
python run_candidate_atlas.py ^
  --epsilon 0.0019 ^
  --centerline-points 16384 ^
  --stations 32 ^
  --angles 32 ^
  --bracket-samples 128 ^
  --no-auto-build ^
  --require-native ^
  --out-dir candidate_atlas_0019_high
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
python run_candidate_convergence.py ^
  --epsilon 0.0019 ^
  --point-counts 4096 8192 16384 ^
  --stations 8 ^
  --angles 16 ^
  --bracket-samples 96 ^
  --no-auto-build ^
  --require-native ^
  --out-dir convergence_0019
```

For the non-trivial knots at the corrected high-resolution gate:

```bat
python run_candidate_convergence.py ^
  --knots 3_1 4_1 5_2 ^
  --epsilon 0.0019 ^
  --point-counts 8192 16384 32768 ^
  --stations 8 ^
  --angles 16 ^
  --no-auto-build ^
  --require-native ^
  --out-dir convergence_0019_high
```

Weak certification requires the candidate branch to occur at at least three resolutions and satisfy

\[
E_\rho<10^{-3},\qquad
E_{R_F}<10^{-3},\qquad
E_\beta<10^{-3}.
\]

Strong certification uses \(10^{-4}\).

## 4. Bifurcation atlas

The primary v0.4.3 scan window is

\[
0.00180\leq\epsilon/r_c\leq0.00210.
\]

```bat
python run_bifurcation_atlas.py ^
  --epsilon-start 0.00180 ^
  --epsilon-stop 0.00210 ^
  --epsilon-step 0.000025 ^
  --resolution-mode adaptive ^
  --target-ds-over-epsilon 0.5 ^
  --min-centerline-points 32768 ^
  --max-centerline-points 65536 ^
  --stations 8 ^
  --angles 16 ^
  --no-auto-build ^
  --require-native ^
  --out-dir bifurcation_atlas
```

This tracks branches by knot, station, angular sector, and nearest \(\rho_\star\). The reported threshold shift is diagnostic until the branch itself passes the convergence run.

## 5. Independent knot-scale sweep

The Fourier source normalization \(D=1\) is not a physical identification with \(r_c\). Test the scale dependence explicitly:

```bat
python run_scale_sweep.py ^
  --scales 0.5 1.0 2.0 4.0 ^
  --epsilon 0.0019 ^
  --resolution-mode adaptive ^
  --target-ds-over-epsilon 1.0 ^
  --min-centerline-points 4096 ^
  --max-centerline-points 65536 ^
  --stations 8 ^
  --angles 16 ^
  --no-auto-build ^
  --require-native ^
  --out-dir scale_sweep_0019
```

The relevant local/non-local geometry changes with

\[
\frac{D_K}{\epsilon}
=
\frac{\texttt{scale\_over\_rc}}{\epsilon/r_c}.
\]

## 6. Symmetry audit

```bat
python run_symmetry_audit.py ^
  --epsilon 0.0019 ^
  --centerline-points 4096 ^
  --no-auto-build ^
  --require-native ^
  --out-dir symmetry_audit
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

They are useful for reproducing v0.3 outputs, but the v0.4.x root solver should be used for candidate claims.

## Performance notes

The native Jacobian kernel performs substantially more arithmetic than the field-only kernel. Candidate discovery batches all radial probes, and bisection refines all active brackets together. Nevertheless, high-resolution runs with \(N=32768\), many stations, and many angular sectors can require significant RAM and runtime.

Recommended sequence: use `START_V043_FULL_CAMPAIGN.bat`. It encodes the audited order, writes per-step logs, and resumes after interruption.

## What v0.4.3 can and cannot conclude

v0.4.3 can distinguish among:

```text
candidate disappears under refinement
candidate is a universal core-profile feature
candidate remains knot-geometry dependent after convergence
```

v0.4.3 does not yet integrate or shoot a complete closed Fermat orbit. That belongs to a later geodesic/monodromy release after the local branches survive certification.
