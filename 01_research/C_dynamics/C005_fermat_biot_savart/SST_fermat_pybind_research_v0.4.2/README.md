# SST Fermat pybind research v0.4.2

Standalone Python + C++17/pybind11 Research-Track harness for the four fixed ideal-knot centerlines

\[
0_1,\qquad 3_1,\qquad 4_1,\qquad 5_2.
\]

The package does **not** import, modify, or patch SSTcore.

## Release purpose

v0.4.2 is the clock-domain hotfix and completion release for the v0.4 candidate-certification campaign. It preserves the v0.4.1 command structure while correcting the bifurcation failure that occurred at

\[
\epsilon/r_c=0.00180.
\]

The v0.4.1 failure came from evaluating

```python
(1.0 - beta_squared) ** 1.5
```

before checking whether

\[
S^2=1-\lVert\boldsymbol\beta\rVert^2>0.
\]

For negative `S2`, Python created a complex value and `max(complex, float)` raised a `TypeError`.

v0.4.2 instead solves the stationary equation through the real-domain numerator

\[
G(\rho)
=
S^2
+
\rho\,\boldsymbol\beta\cdot
\left(J_\beta\mathbf e_\rho\right),
\]

where

\[
J_{\beta,ij}=\frac{\partial\beta_i}{\partial x_j}.
\]

Only after the explicit gate

\[
S^2>0
\]

is the derivative

\[
\frac{\partial R_F}{\partial\rho}
=
\frac{G}{S^3}
\]

evaluated. Transitions between invalid and valid clock domains are recorded as

```text
CLOCK_BOUNDARY_BRACKET
```

and are never counted as stationary roots.

## What is included

- exact Python and C++ Jacobians of the discretized Rosenhead midpoint Biot--Savart kernel;
- clock-safe radial bracket discovery and batch bisection;
- local maximum/minimum classification from the sign change of `G`;
- candidate atlases for `0_1`, `3_1`, `4_1`, and `5_2`;
- three-level branch convergence certification;
- softening bifurcation atlas;
- independent knot-scale sweep;
- reach diagnostics, explicitly marked non-rigorous;
- translation, rotation, cyclic-reindex, orientation-reversal, and mirror covariance audits;
- chunked ideal-knot Fourier evaluation for 32768--65536 point centerlines;
- a campaign runner with `hotfix`, `smoke`, and `full` presets.

## Source provenance

The bundled ideal-knot curves remain the Fourier reconstructions from the uploaded `ideal_favorites.txt` subset:

| SST label | Source ID |
|---|---|
| `0_1` | `0:1:1` |
| `3_1` | `3:1:1` |
| `4_1` | `4:1:1` |
| `5_2` | `5:1:2` |

The uploaded v0.4.1 artifact contained campaign results and logs, not the v0.4.1 source tree. Therefore this release is a full reconstructed v0.4.2 source package based on the available v0.3.0 source plus the observed v0.4.1 CLI/output contract. It is not represented as a byte-for-byte patch of an unavailable v0.4.1 source archive.

## Build

Activate the intended virtual environment, then run:

```bat
python -m pip install -r requirements.txt
python -m fermat_ext.build_ext_if_needed --force --strict
```

A successful Windows build should produce a module resembling:

```text
fermat_ext\_fermat_native.cp314-win_amd64.pyd
```

Do not copy a `.pyd` from an older release: the native binding now includes the field-and-Jacobian API.

## Native audit

```bat
python run_all_checks.py --out-dir audit_out_native --no-auto-build --require-native
```

The audit checks:

- the external analytic radial benchmark;
- Python/C++ radial parity;
- Rankine classifications;
- field parity;
- analytic Jacobian parity;
- finite-difference Jacobian agreement;
- the `0_1` stationary-root control;
- the explicit invalid-clock regression at `epsilon=0.0010`;
- clock-boundary classification without complex arithmetic;
- ideal-knot source-length reconstruction;
- approximate circle-reach diagnostics;
- symmetry covariance;
- preservation of the closed-orbit and QSM epistemic guards.

## Rerun only the failed v0.4.1 step

This is the direct continuation command:

```bat
python run_bifurcation_atlas.py --epsilon-start 0.00180 --epsilon-stop 0.00210 --epsilon-step 0.000025 --resolution-mode adaptive --target-ds-over-epsilon 0.5 --min-centerline-points 32768 --max-centerline-points 65536 --round-centerline-points-to 1024 --stations 8 --angles 16 --bracket-samples 96 --out-dir bifurcation_atlas --no-auto-build --require-native
```

Expected outputs:

```text
bifurcation_atlas\bifurcation_atlas.json
bifurcation_atlas\bifurcation_atlas.csv
bifurcation_atlas\bifurcation_thresholds.json
```

Rows below the real-clock boundary now report invalid probe counts and `CLOCK_BOUNDARY_BRACKET` entries instead of terminating the run.

## Candidate atlas

```bat
python run_candidate_atlas.py --epsilon 0.0019 --centerline-points 8192 --stations 8 --angles 16 --bracket-samples 96 --out-dir candidate_atlas_0019 --no-auto-build --require-native
```

The solver directly resolves

\[
G(\rho;s,\theta)=0,
\]

rather than identifying minima solely from sampled values of `rho/S`.

Pre-convergence minima are labelled:

```text
RESOLVED_LOCAL_MINIMUM
```

not `CERTIFIED_LOCAL_MINIMUM`.

## Candidate convergence

```bat
python run_candidate_convergence.py --knots 3_1 4_1 5_2 --epsilon 0.0019 --point-counts 8192 16384 32768 --stations 8 --angles 16 --bracket-samples 96 --out-dir convergence_0019_high --no-auto-build --require-native
```

For the final two levels, the reported relative errors are

\[
E_\rho,
\qquad
E_{R_F},
\qquad
E_\beta.
\]

The default gates are:

\[
\max(E_\rho,E_{R_F},E_\beta)<10^{-3}
\]

for weak certification and

\[
\max(E_\rho,E_{R_F},E_\beta)<10^{-4}
\]

for strong certification. A branch must occur on at least three resolution levels.

## Scale sweep

```bat
python run_scale_sweep.py --scales 0.5 1.0 2.0 4.0 --epsilon 0.0019 --resolution-mode adaptive --target-ds-over-epsilon 1.0 --min-centerline-points 4096 --max-centerline-points 65536 --round-centerline-points-to 1024 --stations 8 --angles 16 --bracket-samples 96 --out-dir scale_sweep_0019 --no-auto-build --require-native
```

This separates the ideal-knot coordinate scale from the core-softening scale. No physical identification

\[
D_{\rm source}=1\Longrightarrow D_{\rm physical}=r_c
\]

is assumed.

## Symmetry audit

```bat
python run_symmetry_audit.py --epsilon 0.0019 --centerline-points 4096 --out-dir symmetry_audit --no-auto-build --require-native
```

For orientation reversal, the field and Jacobian must change sign while scalar clock quantities remain invariant. Under a mirror transformation, the velocity is treated as an axial vector.

## Campaign runner

Rerun only the failed bifurcation stage:

```bat
python run_campaign.py --preset hotfix
```

Run a small pipeline:

```bat
python run_campaign.py --preset smoke
```

Run the full certification campaign:

```bat
python run_campaign.py --preset full
```

## Scientific boundary

This package may certify a converged radial stationary branch in a sampled transported normal plane. It does not establish:

- a globally closed Fermat geodesic;
- a photon sphere in the relativistic sense;
- a stable Floquet orbit;
- a quasinormal-mode pole.

Every relevant output therefore retains:

```json
"global_closed_orbit_certified": false,
"qsm_certified": false
```

The next major research release remains global Hamiltonian Fermat-geodesic shooting and monodromy/Floquet analysis.