# SST Local Thread Texture + Boost Invariance Blind Falsifier v0.2.2

> **v0.2.2 Windows native-build hotfix.** v0.2.1 fixed setuptools flat-layout discovery. The next real MSVC run exposed a second independent build issue: an absolute `cpp/native.cpp` path caused setuptools to mirror the entire repository path into the object-file directory, exceeding the practical Windows/MSVC path limit and producing C1083. v0.2.2 uses the relative source `cpp/native.cpp` plus the short `build\temp_native` object directory. Physics and gate definitions are unchanged from v0.2.0.


Blind Python/C++17/pybind11 workbench for the **explicit closed-vortex-thread** version of the SST local-background hypothesis.

v0.2.2 replaces the v0.1 prescribed curl-free radial/affine velocity proxies with actual closed vortex filaments evaluated by the same regularized Biot--Savart kernel that evolves the knot/link.

## Target hypothesis

The package does **not** assume a single globally stationary ether frame.  It tests the more local architecture:

1. a source-generated background consists of bundles of vortex threads;
2. over a particle-sized laboratory patch, a large source such as Earth is approximated by locally parallel radial threads;
3. every vortex thread is closed through a remote return path, so no vorticity line terminates;
4. a common boost of knot + complete local thread substrate is intrinsically unobservable;
5. local thread density, orientation and gradients may affect knot dynamics;
6. a second nonparallel bundle provides an Earth-like + Sun-like local superposition test;
7. the physical core radii are held fixed while spatial resolution is changed.

The local approximation is deliberate.  A particle-scale knot has a size enormously smaller than Earth or Sun, so a radial source field is locally parallel.  v0.2.2 therefore does **not** place a fictitious Earth center only a few knot radii away.

## One-click Windows use

Default dataset:

```text
..\..\KnotPlot\knots\final
```

Basic chain:

```cmd
run_all.cmd
```

or explicitly:

```cmd
run_all.cmd "C:\workspace\projects\SST-Workbench\KnotPlot\knots\final"
```

Extended fixed-core convergence ladder:

```cmd
run_all_extended.cmd
```

High-resolution ladder:

```cmd
run_all_highres.cmd
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
run_python_reference.cmd
```

## What changed relative to v0.1.0

v0.1.0 used a radial prescribed velocity proxy and a trace-free affine strain proxy.  Those were useful infrastructure tests, but neither represented an explicit vortex-thread substrate.  v0.2.2 changes the physics layer:

- explicit closed vortex filaments instead of imposed velocity texture;
- no terminating vorticity lines;
- locally parallel source-thread bundles with remote return flux;
- multi-step nonlinear RK2 evolution instead of a single Euler step;
- knot self-induced velocity is recomputed at every RK2 substep;
- primary + secondary nonparallel thread bundles;
- circulation-weight density-gradient bundle;
- return-flux convergence gate;
- same hidden orientation set for every topology;
- fixed core radii relative to a resolution-independent reference radius of gyration;
- C++ kernel accelerates both field evaluation and the full multi-step evolution.

## Dynamical equations

For a set of polygonal vortex filaments, the regularized discrete Biot--Savart field is

\[
\mathbf v(\mathbf x)
=
\frac{1}{4\pi}
\sum_c \Gamma_c
\sum_{j\in c}
\frac{
\Delta\boldsymbol\ell_j\times
(\mathbf x-\mathbf x_{j+1/2})
}{
\left(|\mathbf x-\mathbf x_{j+1/2}|^2+a_c^2\right)^{3/2}
}.
\]

For knot/link points \(\mathbf X_i\), v0.2.2 evolves

\[
\frac{d\mathbf X_i}{dt}
=
\mathbf v_{\rm knot}[\mathbf X(t)](\mathbf X_i)
+
\mathbf v_{\rm threads}(\mathbf X_i,t)
+
\mathbf U_0.
\]

The thread geometry is source-anchored/frozen in its own co-moving frame.  Under a common boost,

\[
\mathbf T_a(t)=\mathbf T_a(0)+\mathbf U_0 t,
\]

so the complete physical system is translated, not the knot alone.

Time integration uses midpoint RK2:

\[
\mathbf k_1=\mathbf F(\mathbf X_n,t_n),
\]

\[
\mathbf k_2=\mathbf F\!\left(\mathbf X_n+\frac{\Delta t}{2}\mathbf k_1,
 t_n+\frac{\Delta t}{2}\right),
\]

\[
\mathbf X_{n+1}=\mathbf X_n+\Delta t\,\mathbf k_2.
\]

This is genuinely nonlinear in the knot geometry because \(\mathbf v_{\rm knot}[\mathbf X(t)]\) is recomputed after the geometry changes.

## Closed local thread bundle

Each local source thread has a straight outgoing leg approximately parallel to a committed local source direction \(\mathbf n\).  The line is closed by a distant return leg with smooth stadium-like connectors.

Thus every component is a closed polygonal curve

\[
C_a:S^1\rightarrow\mathbb R^3,
\]

and its ideal line-vorticity distribution has no endpoints.  In distributional form,

\[
\nabla\cdot\boldsymbol\omega=0
\]

is therefore compatible with the filament topology.

The remote closure is not allowed to define the local result.  v0.2.2 repeats the same local outgoing legs with progressively more distant return paths and tests convergence.

## Fixed-core convention

v0.1.0 used a core radius proportional to bead spacing.  That changes the physical regularization when \(N\) changes.

v0.2.2 instead computes a reference radius of gyration \(R_{g,\rm ref}\) from a fixed high-resolution resample of the input file and sets

\[
a_{\rm knot}=\alpha_k R_{g,\rm ref},
\qquad
 a_{\rm thread}=\alpha_t R_{g,\rm ref}.
\]

These radii remain unchanged throughout an \(N\)-ladder.

The geometric velocity/time scales are

\[
U_g=\frac{|\Gamma|}{4\pi R_{g,\rm ref}},
\qquad
\Delta t=f_t\frac{R_{g,\rm ref}}{U_g}.
\]

No SI calibration is inferred from dimensionless KnotPlot centerlines.

## Blind protocol

Each campaign performs:

1. discover and hash all input geometry files;
2. freeze configuration and thresholds in `precommit.json`;
3. construct one hidden orientation set shared by every topology;
4. create opaque case IDs and binary `.npz` case payloads;
5. SHA-256 commit the semantic mapping;
6. run all nonlinear cases while using only opaque case IDs;
7. score pairwise shape distances before semantic unblinding;
8. verify the commitment;
9. reveal gates and generate `unblinded_report.json` and `summary.csv`.

The one-click workflow is a reproducible **procedural blind**.  It is not cryptographic protection against an operator who deliberately opens `secret/semantic_manifest.json` before the run.

## Gates

| Gate | Test | Classification |
|---|---|---|
| G0 | deterministic repeatability of the same committed thread case | structural/numerical |
| G1 | common boost of knot + complete thread substrate gives no intrinsic shape change | structural covariance |
| G2 | rigid translation of knot + threads leaves intrinsic evolution unchanged | structural covariance |
| G3 | rigid rotation of knot + threads leaves intrinsic evolution unchanged | structural covariance |
| G4 | thread components are closed; numerical \(\nabla\cdot(\nabla\times\mathbf v)\) diagnostic is consistent with zero | structural necessity |
| G5 | moving only the remote return flux farther away leaves the local field/evolution convergent | structural locality |
| G6 | primary closed-thread bundle produces a resolved nonlinear knot response | conditional dynamical bridge |
| G7 | committed thread-density gradient changes the response | conditional dynamical bridge |
| G8 | a second nonparallel bundle changes the primary-bundle response | conditional dynamical bridge |
| G9 | response survives a shared hidden orientation ensemble rather than one hand-picked orientation | conditional dynamical bridge |
| G10 | extended mode: G6--G8 converge with \(N\) while core radii remain fixed | resolution/certification |

`overall_structural_status` depends only on G0--G5.  G6--G9 are reported separately as `overall_conditional_bridge_status`.

A bridge PASS means only that this **committed explicit filament model** produced the specified response.  It does not establish that SST uniquely derives the chosen thread density, circulation, source calibration, or gravitational law.

## Orientation control

If \(\{\mathbf n_a\}_{a=1}^M\) is the hidden direction set, exactly the same set is used for every topology.  For each geometry,

\[
R_a=rac{d_{\rm Kabsch}
\bigl(\mathbf X_{\rm self}(T),\mathbf X_{\rm primary,a}(T)\bigr)}{R_{g,\rm ref}}.
\]

The report records

\[
\operatorname{median}(R_a),\quad
\min R_a,\quad
\max R_a,
\]

and the fraction above the precommitted response threshold.

This removes the v0.1.0 confound in which different topologies could receive unrelated random source directions.

## Primary + secondary bundle

The secondary local bundle is generated at a precommitted nonparallel angle.  It is an **Earth-like/Sun-like local geometry test**, not an astronomical SI model:

\[
\mathbf v_{\rm bg}
=
\mathbf v_{\rm primary}
+
\mathbf v_{\rm secondary}.
\]

Because the knot evolution is nonlinear, v0.2.2 does not demand that the final shape responses add linearly.

## Density-gradient test

The gradient case does not create or destroy threads.  It changes circulation weights across the same closed bundle:

\[
\Gamma_a
=
\Gamma_{\rm th}
\max\!\left[
0.05,
1+g\frac{\boldsymbol\delta_a\cdot\mathbf e_g}{R_{\rm bundle}}
\right].
\]

Thus the vorticity topology remains closed while the local vorticity/circulation density becomes nonuniform.

## Return-flux locality

The local outgoing legs are sampled identically in the near/mid/far closure cases.  Only the remote return geometry changes.

G5 checks both

\[
\epsilon_{\rm field}
=
\frac{\|\mathbf v_{\rm mid}-\mathbf v_{\rm far}\|_2}
{\max(\|\mathbf v_{\rm mid}\|_2,\|\mathbf v_{\rm far}\|_2)}
\]

and

\[
\epsilon_{\rm shape}
=
\frac{d_{\rm Kabsch}
(\mathbf X_{\rm mid}(T),\mathbf X_{\rm far}(T))}
{R_{g,\rm ref}}.
\]

Failure means the chosen finite closure is still contaminating the local result and must not be interpreted as a local source-thread prediction.

## Extended / high-resolution ladders

Extended:

\[
N\in\{128,256,512\}.
\]

High resolution:

\[
N\in\{256,512,1024\}.
\]

For G10, the highest-two relative change is evaluated for:

- median primary response;
- density-gradient differential response;
- secondary-bundle response.

The report distinguishes `CERTIFIED_PASS`, `STANDARD_PASS`, and `FAIL` from the precommitted tolerances.

## Dataset formats

Recursive discovery supports:

- `.txt`, `.xyz`, `.dat`, `.csv` containing XYZ triples;
- blank-line-separated multi-component links;
- ASCII `VECT` centerlines;
- JSON `points`, `centerline`, `components`, `curves`, or `xyz` schemas.

Components are uniformly resampled in arclength.  Unsupported files are skipped and recorded rather than silently coerced.

## Output ledger

Each campaign writes:

```text
precommit.json
blind_commitment.json
blind/manifest.json
blind/cases/Cxxxxxx.npz
blind/results/Cxxxxxx.json
blind/results/Cxxxxxx_final.npy
blind_results.json
blind_score.json
secret/semantic_manifest.json
unblinded_report.json
summary.csv
```

Resolution ladders additionally retain a full ledger under each `N.../` directory and write `extended_summary.json`.

## SST constants recorded as provenance

The package records, but does not automatically inject into dimensionless centerline runs:

\[
\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}
=1.09384563\times10^6\ {\rm m\,s^{-1}},
\]

\[
r_c=1.40897017\times10^{-15}\ {\rm m},
\]

\[
\rho_{\text{core}}=3.8934358266918687\times10^{18}\ {\rm kg\,m^{-3}},
\]

\[
\rho_{\!f}=7.0\times10^{-7}\ {\rm kg\,m^{-3}}.
\]

See `REFERENCES.tex` and `MODEL_NOTES.md`.
