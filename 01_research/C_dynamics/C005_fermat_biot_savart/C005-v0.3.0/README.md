# SST Fermat pybind research v0.3.0

Standalone Python + C++17/pybind11 research harness. It does **not** import, modify, or patch SSTcore.

This release upgrades the four-knot matrix

\[
0_1,\qquad 3_1,\qquad 4_1,\qquad 5_2
\]

with explicit softening studies and centerline-resolution diagnostics. It is a Research-Track numerical package, not a CANON claim.

## Main additions in v0.3.0

1. Adaptive centerline point counts based on

   \[
   \frac{\langle\Delta s\rangle}{\epsilon}
   \leq \eta_{\rm target},
   \qquad
   N_{\rm req}
   =
   \left\lceil
   \frac{L_K}{\epsilon\eta_{\rm target}}
   \right\rceil.
   \]

2. A Rosenhead-softening matrix over all four knot classes.
3. A fixed-probe resolution ladder for direct field-convergence checks.
4. A one-dimensional Rankine/Rosenhead/Lamb--Oseen profile matrix.
5. Exact straight-filament Rosenhead threshold diagnostics.
6. Ray-boundary diagnostics distinguishing interior minima from scan-boundary minima.
7. Native/Python full or spot parity modes.
8. Explicit under-resolution reporting when a point cap prevents the requested \(\Delta s/\epsilon\) target.

## Kernel scope

The full three-dimensional knot field currently uses only the regularized midpoint Rosenhead kernel

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

Its implementation name is:

```text
rosenhead_midpoint
```

The Rankine and Lamb--Oseen models are presently implemented only in the **one-dimensional radial profile solver**. They are not silently substituted into the full knot-field kernel.

## Straight Rosenhead reference thresholds

For the infinite straight reference profile

\[
\beta(\rho)
=
\beta_0\frac{\rho}{\rho^2+\epsilon^2},
\]

the maximum speed is

\[
\beta_{\max}=\frac{\beta_0}{2\epsilon}.
\]

Clock degeneracy is avoided when

\[
\epsilon>rac{\beta_0}{2}
=1.8243381393\times10^{-3}.
\]

A radial Fermat-critical point can exist only when

\[
\epsilon
\leq
\sqrt{\frac{8}{27}}\,\beta_0
=1.9860878042\times10^{-3}.
\]

Hence the straight-reference horizon-free critical window is narrow:

\[
1.8243381393\times10^{-3}
<
\frac{\epsilon}{r_c}
\leq
1.9860878042\times10^{-3}.
\]

These thresholds are exact only for the infinite straight reference. Curvature and non-local knot contributions can shift a full-knot result.

## Scientific guard

The local scan evaluates

\[
R_F(\rho;s,\theta)
=
\frac{\rho}{\sqrt{1-\lVert\boldsymbol\beta\rVert^2}}
\]

along transported normal rays. A detected minimum is labelled only:

```text
LOCAL_TRANSVERSE_MINIMUM_CANDIDATE
```

It is not a certification of a closed Fermat geodesic, a photon sphere, a light ring, or a QSM pole. Every output retains:

```json
"global_closed_orbit_certified": false,
"qsm_certified": false
```

## Build native pybind11 module

From the project root in an activated virtual environment:

```bat
python -m pip install -r requirements.txt
python -m fermat_ext.build_ext_if_needed --force --strict
```

After upgrading from v0.2.0, rebuild the extension because the C++ binding signature now includes the explicit kernel-model argument.

## Full audit

```bat
python run_all_checks.py --out-dir audit_out_native --no-auto-build --require-native
```

The audit checks:

- external analytic critical-radius accuracy;
- native/Python radial parity;
- Rankine parity;
- the Rosenhead \(\epsilon=0.0019\) critical case;
- the Rosenhead \(\epsilon=0.0020\) blocked case;
- all four ideal-knot centerlines;
- native/Python full-field parity for the four-knot smoke matrix;
- adaptive resolution-plan generation;
- a minimal four-knot softening-pipeline smoke test;
- preservation of all epistemic guards.

## 1. Four-knot matrix with adaptive resolution

At the previously used \(\epsilon/r_c=0.0045\), target

\[
\langle\Delta s\rangle/\epsilon\lesssim1
\]

requires approximately:

| Knot | Selected centerline points |
|---|---:|
| `0_1` | 1408 |
| `3_1` | 3648 |
| `4_1` | 4688 |
| `5_2` | 5504 |

Run:

```bat
python run_knot_matrix.py --preset smoke --adaptive-resolution --target-ds-over-epsilon 1.0 --max-centerline-points 8192 --epsilon 0.0045 --no-auto-build --require-native --out-dir knot_matrix_adaptive
```

The probe preset and centerline resolution are independent: adaptive mode changes the centerline point count per knot while preserving the selected probe grid.

## 2. Softening matrix

### Fast first run

```bat
python run_softening_matrix.py --preset smoke --epsilon-values 0.0015 0.0019 0.0020 0.0025 0.0045 --parity-mode spot --no-auto-build --require-native --out-dir softening_smoke
```

### Full default threshold scan

```bat
python run_softening_matrix.py --preset standard --parity-mode spot --no-auto-build --require-native --out-dir softening_standard
```

Default epsilon values are:

```text
0.0010 0.0015 0.0018 0.00185 0.0019 0.00195 0.0020 0.0025 0.0035 0.0045
```

Parity modes:

- `full`: Python and C++ evaluate the complete scan grid;
- `spot`: complete native scan plus a deterministic reduced Python/C++ parity grid;
- `none`: primary backend only.

For large adaptive point counts, `spot` is the recommended default.

## 3. Resolution ladder

The convergence ladder fixes the physical probe locations using the highest-resolution centerline. Lower-resolution centerlines are evaluated at exactly those same probes.

```bat
python run_resolution_ladder.py --epsilon 0.0045 --point-counts 1024 2048 4096 8192 --no-auto-build --require-native --out-dir resolution_0045
```

For the critical window, a higher cap may be necessary:

```bat
python run_resolution_ladder.py --epsilon 0.0019 --point-counts 2048 4096 8192 16384 --no-auto-build --require-native --out-dir resolution_0019
```

The largest point count is a finite-resolution reference, not an independent continuum proof.

## 4. Radial profile matrix

```bat
python run_profile_matrix.py --profiles rankine rosenhead lamb_oseen --no-auto-build --out-dir profile_matrix
```

This separates core-profile dependence from knot geometry before any full-knot kernel generalization is attempted.

## Resolution presets for the softening matrix

| Preset | Stations | Angles | Radial samples | Target \(\Delta s/\epsilon\) | Point cap |
|---|---:|---:|---:|---:|---:|
| `smoke` | 2 | 6 | 48 | 2.0 | 4096 |
| `standard` | 4 | 12 | 96 | 1.0 | 8192 |
| `high` | 8 | 24 | 192 | 0.5 | 16384 |

When the cap is reached, outputs explicitly report:

```text
CAPPED_UNDERRESOLVED_BY_PLAN
```

A candidate detected in an under-resolved row must not be promoted until it survives a resolution ladder.

## Output overview

`run_softening_matrix.py` writes:

```text
softening_matrix.json
softening_matrix.csv
epsilon_*/0_1_primary.json
epsilon_*/3_1_primary.json
epsilon_*/4_1_primary.json
epsilon_*/5_2_primary.json
epsilon_*/*_parity.json
```

Cross-knot fields include:

- epsilon regime relative to the straight Rosenhead thresholds;
- selected centerline point count;
- mean and maximum \(\Delta s/\epsilon\);
- target-met or capped-underresolved status;
- local candidate count;
- invalid-clock count;
- maximum \(\lVert\boldsymbol\beta\rVert\);
- interior versus scan-boundary minimum counts;
- native/Python parity status.

## Next research gate

After softening and discretization robustness are established, the next non-local stage remains:

\[
\text{Hamiltonian Fermat-geodesic shooting}
\rightarrow
\text{monodromy/Floquet analysis}
\rightarrow
\text{open-wave QSM solver}.
\]