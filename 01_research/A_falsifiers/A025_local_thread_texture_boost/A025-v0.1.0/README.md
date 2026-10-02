# SST Local Thread Texture + Boost Invariance Blind Falsifier v0.1.0

Blind Python/C++17/pybind11 workbench for the hypothesis:

1. a **uniform common boost is intrinsically unobservable** to a closed vortex filament;
2. source-generated background structure is local and geometric rather than a single global ether wind;
3. only a non-uniform/background-texture coupling may alter intrinsic knot/link geometry.

The package follows the established `SST_cpp_pybind_audit_template` pattern: `cpp/native.cpp`, Python fallback, source-hash native rebuild, `--force-python`, strict native self-test, JSON/CSV audit outputs, and one-click Windows runners.

## One-click Windows use

From the package directory:

```cmd
run_all.cmd
```

Default dataset:

```text
..\..\KnotPlot\knots\final
```

Or explicitly:

```cmd
run_all.cmd "C:\workspace\projects\SST-Workbench\KnotPlot\knots\final"
```

Extended convergence ladder:

```cmd
run_all_extended.cmd
```

Individual runners:

```cmd
run_install.cmd
run_build_native.cmd
run_selftest.cmd
run_quick.cmd
run_basic.cmd
run_extended.cmd
run_python_reference.cmd
```

## Blind protocol

Each campaign performs the following sequence automatically and without result-dependent retuning:

1. load and uniformly arclength-resample each accepted knot/link;
2. freeze thresholds and input hashes in `precommit.json`;
3. generate randomized opaque case IDs;
4. write a SHA-256 commitment to the semantic case map;
5. run all cases using only opaque numerical case files;
6. score pairwise intrinsic shape differences while still blinded;
7. verify the commitment and only then reveal semantic gate labels.

The secret mapping is placed under `secret/semantic_manifest.json`. For a strict two-person blind workflow, the operator can move that file away after preparation and restore it only for unblinding. The automated one-click workflow is a reproducible **procedural blind**, not cryptographic protection against an operator intentionally inspecting the secret.

## Core equations

The filament self-velocity uses a regularized Biot--Savart discretization,

\[
\mathbf v_i = \frac{\Gamma}{4\pi}
\sum_j
\frac{\Delta\boldsymbol\ell_j\times(\mathbf x_i-\mathbf x_{j+1/2})}
{\left(|\mathbf x_i-\mathbf x_{j+1/2}|^2+a^2\right)^{3/2}}.
\]

A common boost is

\[
\mathbf v_i\mapsto \mathbf v_i+\mathbf U_0.
\]

After one time step,

\[
\mathbf x_i' = \mathbf x_i+\Delta t\left(\mathbf v_i+\mathbf U_0\right),
\]

so the boost contributes only a rigid translation \(\Delta t\,\mathbf U_0\). The intrinsic Kabsch-aligned RMS shape distance must therefore remain numerically zero.

The source-generated radial proxy is

\[
\mathbf v_{\rm src}(\mathbf x)
= q\frac{\mathbf r}{\left(r^2+a_s^2\right)^{3/2}}
-\left\langle q\frac{\mathbf r}{\left(r^2+a_s^2\right)^{3/2}}\right\rangle,
\qquad
\mathbf r=\mathbf x-\mathbf x_s.
\]

Away from the source, the unregularized field \(\mathbf r/r^3\) is divergence-free. The mean is removed deliberately so that the test isolates spatial texture/tidal structure rather than common translation.

A second, explicitly conditional director proxy uses

\[
S_{ij}=n_i n_j-\frac13\delta_{ij},
\qquad
\mathbf v_{\rm dir}=A\,\mathbf S\frac{\mathbf x-\mathbf x_c}{R_g}.
\]

Because \(\mathrm{tr}\,\mathbf S=0\), this affine proxy is incompressible.

## Gates

| Gate | Requirement | Status class |
|---|---|---|
| G0 | zero-background duplicate recovers identical intrinsic evolution | structural null |
| G1 | uniform common boost produces no intrinsic shape change | structural null |
| G2 | rigid translation of knot + source leaves result invariant | covariance null |
| G3 | rigid rotation of knot + source leaves result invariant | covariance null |
| G4 | radial source-texture proxy produces resolvable deformation | conditional bridge |
| G5 | director-tensor proxy produces resolvable deformation | conditional bridge |
| G6 | \(+A/-A\) radial response has the expected one-step symmetry | numerical bridge check |
| G7 | radial response scales linearly with small imposed amplitude | numerical bridge check |

A structural PASS is necessary for the proposed "no global absolute velocity, but local objective texture" architecture. It is **not** evidence that the radial/director proxy is the SST physical law. G4--G7 are intentionally labelled conditional until a canon-derived thread-to-knot coupling replaces the proxy in `backgrounds.py`.

## Extended mode

`run_all_extended.cmd` runs a blind resolution ladder

\[
N\in\{128,256,512\}
\]

and requires both the structural null/covariance gates and convergence of the radial conditional response between the two highest resolutions.

## Dataset parsing

Recursive discovery supports:

- `.txt`, `.xyz`, `.dat`, `.csv` containing XYZ triples;
- blank-line-separated multi-component links;
- standard ASCII `VECT` centerlines;
- simple JSON `points`, `centerline`, `components`, or `curves` schemas.

Every accepted component is closed and resampled uniformly in arclength before the campaign. Unsupported/ambiguous files are skipped and recorded in `blind/manifest.json` instead of being silently coerced.

## Output ledger

Each campaign writes:

```text
precommit.json
blind_commitment.json
blind/manifest.json
blind/cases/Cxxxxxx.npz
blind/results/Cxxxxxx.json
blind_results.json
blind_score.json
secret/semantic_manifest.json
unblinded_report.json
summary.csv
```

Extended runs additionally write `extended_summary.json` and retain each resolution's complete blind ledger under `N128/`, `N256/`, and `N512/`.

## Dimensional convention

Input centerline coordinates may be dimensionless. The campaign therefore uses the geometric velocity scale

\[
U_g=\frac{|\Gamma|}{4\pi R_g},
\qquad
\Delta t=f_t\frac{R_g}{U_g},
\]

so all response thresholds are dimensionless ratios such as `shape_rms / R_g`. SST canonical SI constants are recorded as provenance but are not mixed into dimensionless centerline data unless an explicit physical length/circulation calibration is supplied in a future version.

## Epistemic guard

The workbench falsifies numerical and structural consequences of a specified coupling. It must not be used to claim that a source-generated vortex-thread substrate has been derived merely because the conditional proxy gates pass.
