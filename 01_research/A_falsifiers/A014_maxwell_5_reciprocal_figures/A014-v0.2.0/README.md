# 5_Maxwell_SST_Reciprocal_Falsifier_v0.2.0

Blind Maxwell–SST reciprocal-stress workbench for the `5_` Maxwell branch.

Primary input directory on the SST Workbench layout:

```text
..\..\KnotPlot\knots\final
```

The package consumes the shared-final pairs

```text
*_final.txt
*_final.metrics.json
```

without modifying the KnotPlot data.

## What v0.2.0 tests

For a resolved contact/kink rigidity matrix \(A_K\) and non-negative multipliers \(\Lambda\), the first-order audit is

\[
-\nabla L + A_K\Lambda \simeq 0,
\qquad \Lambda\ge 0,
\]

where the current declared energy gradient is the polygonal length gradient. This is a contact-mechanics audit; it is **not** silently promoted to a complete SST energy functional.

The workbench records:

1. global KKT/equilibrium residual \(\chi_{\mathrm{KKT}}\);
2. vertex-local reciprocal-force closure;
3. numerical rank, right nullity and left nullity;
4. positive self-stress feasibility
   \[
   \mathcal C_+(A_K)=\ker A_K\cap\mathbb R_{\ge0}^{M};
   \]
5. the positive singular-value ratio
   \[
   \zeta_K=\frac{\sigma_{\min}^{+}}{\sigma_{\max}};
   \]
6. duplicate/redundant constraint channels;
7. random 2-D projection closure checks;
8. SST force–area coherence;
9. contact-shell sensitivity in `extended` mode;
10. small-coordinate-perturbation sensitivity when a case is already preregistered as near-singular.

A strict Maxwell reciprocal polyhedron is deliberately **not** required for mechanical success. Maxwell explicitly distinguishes mechanical solvability from the existence of a perfect reciprocal figure; redundant force diagrams may remain possible.

## v0.2.0 native acceleration

This release is rebuilt around the supplied `SST_cpp_pybind_audit_template` pattern:

```text
cpp/5_maxwell_native.cpp
maxwell5_native/build_ext_if_needed.py
maxwell5_native/_native*.pyd
```

The C++17 pybind11 kernel performs the expensive geometry work:

- component-aware segment construction;
- multithreaded nonlocal segment-pair search;
- active contact-shell extraction;
- discrete curvature/kink search;
- sparse rigidity-matrix assembly;
- polygonal length-gradient assembly.

`5_run_basic.cmd` and `5_run_extended.cmd` use `--require-native`; they do not silently fall back to slow Python after installation.

The number of C++ search threads defaults to `%NUMBER_OF_PROCESSORS%`. Override it with the first argument, for example:

```bat
5_run_basic.cmd 16
5_run_extended.cmd 16
```

## Critical v0.2.0 data-format fix

The shared-final link files can concatenate multiple components **without blank separator lines**. v0.2.0 therefore does not infer link components from text formatting. It reads the authoritative

```json
"vertices_per_component": [300, 300, ...]
```

from the paired `*.metrics.json` before blinding and passes only the sanitized component counts to the numerical runner.

This prevents a multi-component link from being misread as one closed polygon.

## Contact inference

When an explicit contact sidecar is absent, the C++ adapter reconstructs a candidate contact shell around the declared Ridgerunner thickness \(a\):

\[
2a(1-\varepsilon_c)
\le d_{ij}
\le
2a(1+\varepsilon_c).
\]

The preregistered baseline is

\[
\varepsilon_c=10^{-4}.
\]

This is intentionally a **shell**, not the old one-sided condition \(d\le 2a(1+\varepsilon_c)\), because the latter incorrectly admitted thousands of short-range same-curve neighbors.

`extended` mode repeats the contact inventory over a frozen tolerance ladder. Results that are unstable under this ladder must not be interpreted as contact-topology invariants.

### Ridgerunner quality gate

The shared-final metrics are used before blinding to set a single boolean numerical-QC flag. The preregistered default is

\[
\mathrm{RR\ residual}\le 0.05.
\]

Cases above that threshold are **still visited and inventoried**, but rank/self-stress/equilibrium interpretation is refused with

```text
GEOMETRY_QC_REFUSED_EQUILIBRIUM
```

rather than treating an under-relaxed geometry as an SST falsification.

The physical identity is hidden; only the QC eligibility bit enters the blinded numerical run.

## SST force–area normalization

The package checks the existing v0.8.35 coherence identity

\[
F_{\mathrm{swirl}}^{\max}
=
\pi r_c^2\,\rho_{\mathrm{horn}}^{\mathrm{eff}}
\left\lVert\mathbf v_{\!\boldsymbol{\circlearrowleft}}\right\rVert^2.
\]

With

\[
\Pi_\star
=
\rho_{\mathrm{horn}}^{\mathrm{eff}}
\left\lVert\mathbf v_{\!\boldsymbol{\circlearrowleft}}\right\rVert^2,
\qquad
\mathbf A^\star=\frac{\mathbf F}{\Pi_\star},
\]

one obtains

\[
\frac{A^\star}{\pi r_c^2}
=
\frac{F}{F_{\mathrm{swirl}}^{\max}}.
\]

Length-minimization KKT multipliers are **not** converted into newtons unless a physical force scale was preregistered independently.

## Ready-to-run Windows commands

### 1. Install + native build + controls

```bat
5_run_install.cmd
```

This uses the shared SST Workbench virtual environment:

```text
..\..\.venv
```

If it does not exist, the installer creates it. It then installs NumPy, SciPy, pybind11 and setuptools, builds the C++ extension and runs the regression controls.

For MSVC, install Visual Studio Build Tools with **Desktop development with C++**.

### 2. Basic campaign

```bat
5_run_basic.cmd
```

or explicitly:

```bat
5_run_basic.cmd 16
```

The basic set is a representative, geometry-QC-qualified subset of the shared-final knot/torus files.

Override the data directory:

```bat
5_run_basic.cmd 16 D:\other\knots\final
```

### 3. Extended campaign

```bat
5_run_extended.cmd 16
```

This scans **all** `*_final.txt` files in `..\..\KnotPlot\knots\final`.

- QC-qualified geometries receive the complete equilibrium/rank/self-stress audit.
- under-relaxed geometries receive contact/kink inventory plus an explicit QC refusal.
- tolerance robustness is evaluated on qualified geometries;
- coordinate perturbations are only activated by the preregistered near-singular trigger.

### 4. Run everything

```bat
5_run_all.cmd 16
```

This performs install/tests, then basic, then extended.

### 5. Native benchmark

```bat
5_run_benchmark.cmd 16
```

This compares the C++ pybind contact kernel with the pure-Python correctness fallback on `knot_3.1_final`.

### 6. Custom mode

```bat
5_run_custom.cmd basic
5_run_custom.cmd extended ..\..\KnotPlot\knots\final 16
```

## Blind workflow

The CMD wrappers execute the same pipeline:

```text
private shared-final identities
        |
        v
5_make_manifest.py
        |
        v
prepare_blind.py  ----> private_blind_key.json   [kept outside blind_campaign]
        |
        v
blind_manifest.json + CASE_* data
        |
        v
run_blind.py --require-native
        |
        v
frozen numerical results
        |
        v
unblind.py
        |
        v
unblinded_summary.json / .csv / REPORT.md
```

The blind runner refuses to run if a private mapping file is placed inside the blind campaign directory.

## Output structure

A basic run creates, for example,

```text
outputs_basic_YYYYMMDD_HHMMSS/
├── datasets.private.json
├── private_blind_key.json
├── blind_campaign/
│   ├── blind_manifest.json
│   ├── data/
│   └── results/
│       ├── frozen_preregistration.json
│       ├── blind_summary.json
│       ├── convergence.json
│       └── CASE_*/
│           ├── metrics.json
│           └── native/
│               ├── A.npz
│               ├── b_length_gradient.npy
│               ├── contacts.csv
│               ├── kinks.csv
│               └── native_metrics.json
├── unblinded_summary.json
├── unblinded_summary.csv
└── REPORT.md
```

## Interpretation guards

- `FAIL` of the length-KKT equilibrium gate falsifies **that declared contact/length closure on that geometry**, not all SST dynamics.
- `ker(A_K^T)` is a contact-network mechanism diagnostic unless the complete mechanical model is explicitly declared.
- `strict_reciprocity_gate=UNTESTED_NO_DUAL_CELL_INCIDENCE` is not a failure.
- poor Ridgerunner residuals are a geometry-QC issue, not physical evidence.
- contact-shell sensitivity is reported rather than hidden.
- no target rank such as `9` enters the optimizer, contact extraction, stopping criterion or case selection.

## Canon patch

The package includes the research-track-safe patch:

```text
5_SST_CANON-v0.8.35-Maxwell-reciprocal-stress.diff
```

It retains Maxwell reciprocity as a geometric/mechanical research diagnostic and preserves the guard that mechanical equilibrium can exist without a perfect reciprocal complex.

## Reference

```latex
\bibitem{Maxwell1864Reciprocal}
J.~C. Maxwell,
``On Reciprocal Figures and Diagrams of Forces,''
\emph{The London, Edinburgh, and Dublin Philosophical Magazine
and Journal of Science}, Series~4, \textbf{27}(182), 250--261 (1864).
\href{https://doi.org/10.1080/14786446408643663}
{doi:10.1080/14786446408643663}.
```
