# SST Local Thread Texture + Boost Invariance Blind Falsifier v0.3.0

Blind Python/C++17/pybind11 workbench for the SST **local source-generated vortex-thread** hypothesis.

This release is based on the user-uploaded v0.2.0 package.  v0.2.0 already had explicit closed vortex filaments, fixed core radii, return flux, shared hidden orientations and nonlinear evolution.  v0.3.0 therefore focuses on the numerical and physical-admissibility gaps that remained.

## Central falsification target

The workbench distinguishes

\[
\boxed{\text{common translational boost}}
\]

from

\[
\boxed{\text{objective local vortex-thread texture}}.
\]

A uniform common boost of knot + complete local substrate must not create intrinsic deformation after rigid alignment, while gradients, finite source curvature and nonparallel thread bundles may produce local dynamical responses.

The model does **not** assume one globally stationary ether frame.

---

## v0.3.0 numerical core

### Exact finite-core segment kernel

Instead of the v0.2 midpoint approximation, every straight polygon segment is analytically integrated for the Rosenhead-regularized Biot--Savart kernel:

\[
\mathbf v(\mathbf x)=
\frac{\Gamma}{4\pi}
\oint
\frac{d\boldsymbol\ell\times(\mathbf x-\mathbf q)}
{\left(|\mathbf x-\mathbf q|^2+a^2\right)^{3/2}}.
\]

Python and C++ contain independent implementations and `run_selftest.py` compares them.

### RK4

v0.2 used midpoint RK2.  v0.3 uses classical RK4 and recomputes both knot self-field and thread field at all four stages.

### Constant final time

The scheduler commits a fixed

\[
T_{\rm final}
\]

before the run.  Spatial resolution is therefore never compared at different integration durations.

### \(\Delta t\propto\Delta s^2\) subcycling

When required by the configured numerical certification bound,

\[
\Delta t_{\max}=C_{\Delta s^2}\frac{\Delta s^2}{|\Gamma|},
\]

an outer RK4 step is subdivided into an integer number of substeps.  `T_final` remains unchanged.

### Arclength reparameterization

After a complete outer RK4 step, each closed knot/link component can be redistributed to uniform polygonal arclength with the same bead count.  No extra restoring term is inserted into the equation of motion.

---

## Physical thread construction

Every background thread is a closed polygonal filament:

\[
C_a:S^1\rightarrow\mathbb R^3.
\]

No vortex line terminates, consistent with the structural requirement

\[
\nabla\cdot\boldsymbol\omega=0.
\]

The primary local source bundle is approximately parallel, representing the particle-scale patch limit of a much larger Earth-/Sun-sized radial source.  Its transverse lattice phase relative to the knot is hidden and shared in normalized form across topologies, so a central thread is not deliberately pinned to the knot centroid.

v0.3 additionally constructs finite-source radial bundles and verifies that

\[
D/R_g\rightarrow\infty
\]

converges to the parallel local model.

---

## Density is no longer conflated with circulation

v0.2 encoded the density-gradient case through circulation weights.  v0.3 separates:

1. **circulation gradient** — same thread positions, different \(\Gamma_a\);
2. **position/number-density gradient** — same per-thread circulation, different local thread spacing.

Both cases use matched total circulation so a response cannot be attributed merely to changing the net committed circulation budget.

---

## Core-overlap audit

For each primary case v0.3 measures the minimum centerline clearance

\[
d_{\min}
\]

and reports

\[
\chi_{\rm clear}
=
\frac{d_{\min}}
{a_{\rm knot}+a_{\rm thread}}.
\]

When finite cores overlap, covariance/closure tests can still be evaluated, but bridge responses are classified `INDETERMINATE` rather than promoted to evidence.

---

## Blind protocol

For each campaign:

1. input geometry files and configuration are hashed;
2. hidden orientation, covariance and source directions are generated;
3. opaque `Cxxxxxx` cases are written;
4. the semantic mapping is SHA-256 committed;
5. nonlinear cases run only from opaque IDs;
6. pairwise shape scores are computed before semantic reveal;
7. commitment is verified;
8. gates are unblinded into `unblinded_report.json` and `summary.csv`.

This is a reproducible **procedural blind**.  It is not cryptographic protection against an operator intentionally opening the secret semantic map before execution.

---

## Gates

| Gate | Test | Classification |
|---|---|---|
| G0 | deterministic repeatability | structural/numerical |
| G1 | common boost of knot + substrate | structural covariance |
| G2 | rigid translation covariance | structural covariance |
| G3 | rigid rotation covariance | structural covariance |
| G4 | closed filament topology + solenoidal diagnostic | structural necessity |
| G5 | knot-thread finite-core clearance | admissibility; overlap -> bridge indeterminate |
| G6 | remote return-flux locality + local-leg identity | structural locality |
| G7 | primary bundle dynamical response | conditional bridge |
| G8 | circulation-gradient vs position-density-gradient decomposition | conditional bridge |
| G9 | primary + nonparallel secondary bundle | conditional bridge |
| G10 | common hidden orientation + transverse lattice-phase ensemble | conditional bridge |
| G11 | finite radial source -> parallel local limit | structural local-geometry test |

Extended/high-resolution runs additionally produce:

\[
\boxed{C1:\text{ spatial fixed-core convergence}}
\]

and

\[
\boxed{C2:\text{ independent temporal RK4 convergence}}.
\]

---

## Default dataset

```text
..\..\KnotPlot\knots\final
```

## Windows one-click runners

Basic campaign:

```cmd
run_all.cmd
```

Extended spatial + temporal certification:

```cmd
run_all_extended.cmd
```

High-resolution certification:

```cmd
run_all_highres.cmd
```

Known difficult holdouts only:

```cmd
run_all_holdout.cmd
```

All accept an optional dataset path:

```cmd
run_all_extended.cmd "C:\workspace\projects\SST-Workbench\KnotPlot\knots\final"
```

Individual runners:

```cmd
run_install.cmd
run_build_native.cmd
run_selftest.cmd
run_quick.cmd
run_basic.cmd
run_extended.cmd
run_highres.cmd
run_holdout_certification.cmd
run_python_reference.cmd
```

---

## Extended certification logic

For a spatial ladder

\[
N_1<N_2<N_3,
\]

all runs use the same physical core ratios and the same `T_final`.  The highest two resolutions define the spatial certification error.

The highest resolution is then rerun with an additional time-refinement factor while keeping the same

\[
N,
\qquad
a_{\rm knot},
\qquad
a_{\rm thread},
\qquad
T_{\rm final}.
\]

This produces a genuinely separate temporal error estimate.

`config/extended.json` defaults to

```text
N = 128 -> 256 -> 512
```

and `config/highres.json` defaults to

```text
N = 256 -> 512 -> 1024
```

The prior-release holdout configuration searches for:

```text
link_0.3.1
torus_6.21
```

and runs the configured high-resolution certification only on matched files.

---

## Main outputs

Single campaign:

```text
precommit.json
blind_commitment.json
blind/manifest.json
blind/cases/Cxxxxxx.npz
blind/results/Cxxxxxx_final.npy
blind_score.json
secret/semantic_manifest.json
unblinded_report.json
summary.csv
```

Extended/high-resolution certification additionally writes:

```text
certification_precommit.json
config_spatial_N*.json
config_temporal_N*_x*.json
spatial_N*/...
temporal_N*_x*/...
extended_summary.json
```

---

## Interpretation guard

A structural PASS verifies that the **committed local thread construction and covariance tests** behaved as required.

A bridge PASS means only that the explicit filament model produced a resolved response above the precommitted threshold.

It does not establish:

- an SST gravitational law;
- the SI thread density of Earth or Sun;
- the correct circulation per background thread;
- that the chosen finite-core filament model is unique;
- that dimensionless KnotPlot coordinates have been calibrated to SI length.

A core-overlap case is reported as `INDETERMINATE` for dynamical bridge interpretation rather than silently counted as support.

---

## Validation status of the packaged release

The packaged Python reference path was syntax checked and exercised on synthetic closed trefoil data.  The release selftest validates:

- exact segment integral against dense numerical quadrature;
- Python/backend field parity interface;
- Python/backend RK4 evolution parity interface;
- common-boost shape null;
- arclength redistribution improvement;
- closed-thread topology;
- monotonic finite-source-to-parallel field convergence.

A native Windows `cpp` PASS is intentionally **not** claimed from the packaging environment because pybind11 headers are not installed there.  `run_all*.cmd` requires a strict native build and `run_selftest.cmd --require-native` on the user's machine before the physical campaign proceeds.

See `CHANGELOG.md`, `MODEL_NOTES.md`, `VALIDATION.md` and `REFERENCES.tex`.
