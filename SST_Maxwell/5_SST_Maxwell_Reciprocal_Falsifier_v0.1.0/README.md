# SST Maxwell Reciprocal-Stress Falsifier v0.1.0

Blind Python/C++ audit package for relaxed finite-thickness knot/contact datasets.

The package tests the research-track consequences suggested by J. C. Maxwell's 1864 reciprocal-force construction **without** assuming that every mechanically admissible SST contact network must possess a strict Maxwell reciprocal polyhedron.

## Scientific scope

For an active strut/kink rigidity matrix \(A\) and non-negative multiplier vector \(\Lambda\), the package audits the first-order balance

\[
-\nabla E + A\Lambda = 0,
\qquad \Lambda\ge 0.
\]

The default energy is polygonal length, so the C++ core writes \(b=\nabla L\) and Python solves \(A\Lambda\simeq b\). A different SST energy can be supplied in a later adapter; the current release must **not** be described as having tested an undeclared full SST energy functional.

The campaign covers six Maxwell/SST questions:

1. **Local reciprocal force closure.** Does the fitted or solver-supplied contact-force system close at every resolved vertex rather than only in one global norm?
2. **Rank / nullspaces.** What are \(\operatorname{rank}A\), \(\dim\ker A\), and \(\dim\ker A^{\mathsf T}\)? The positive self-stress cone
   \[
   \mathcal C_+=\ker A\cap\mathbb R_{\ge0}^{M}
   \]
   is tested by linear programming on the normalized slice \(\sum_j\lambda_j=1\).
3. **SST force--area normalization.** The package verifies the existing v0.8.35 coherence identity
   \[
   F_{\rm swirl}^{\max}=\pi r_c^2\,\rho_{\rm horn}^{\rm eff}\,\lVert\mathbf v_{\!\boldsymbol{\circlearrowleft}}\rVert^2
   \]
   and therefore, only for a force already expressed in newtons,
   \[
   \frac{A^\star}{\pi r_c^2}=\frac{F}{F_{\rm swirl}^{\max}},\qquad
   A^\star=\frac{F}{\rho_{\rm horn}^{\rm eff}\lVert\mathbf v_{\!\boldsymbol{\circlearrowleft}}\rVert^2}.
   \]
   Length-minimization KKT multipliers are **not** silently converted into newtons.
4. **Near-singular / pre-event diagnostic.** The package records
   \[
   \zeta=\frac{\sigma_{\min}^{+}(A)}{\sigma_{\max}(A)}.
   \]
   A small value is a conditioning warning. It is not, by itself, a Kairos event or a dynamical-instability proof.
5. **Strict reciprocity versus redundant force representation.** Missing dual-cell incidence is reported as `UNTESTED`, not as a mechanical failure. Mechanical equilibrium can pass even when a strict Maxwell reciprocal complex is unavailable.
6. **Projection sanity and resolution convergence.** Local closure is projected to fixed random 2-planes as a numerical consistency check, and normalized arclength contact maps are compared across a blinded resolution ladder using a symmetric Hausdorff metric on \(S^1\times S^1\).

## Blind protocol

The private input manifest contains filenames and physical labels. `prepare_blind.py` hashes file content, path, group, and a cryptographic salt into `CASE_*` and `GROUP_*` identifiers and copies only sanitized inputs into the blind campaign. The private mapping is written separately.

The numerical runner refuses to execute if a private mapping file is placed inside the blind campaign directory. Preregistered thresholds are frozen into `results/frozen_preregistration.json` before any case result is produced.

The runner never contains a target value such as `9` in its rank stopping rule or solver objective. A later comparison with a factor-nine SST hypothesis is an **unblinded interpretation step**, not a tuning criterion.

## Geometry provenance guard

The current SST Canon distinguishes:

- original KnotPlot/Ridgerunner audit geometry;
- separately resampled SSTcore/VortexLab geometry.

By default this package refuses to infer the active contact skeleton from a geometry whose `source_role` contains `vortexlab-uniform`, `uniform-n300`, or `downstream-resample`. Such a case is accepted only when it carries an explicit contact sidecar, or when the preregistration explicitly overrides the guard.

This matters because a downstream spline/resampling step can change curvature and apparent contact distances while the original Ridgerunner polish remains the constrained audit geometry.

## Input formats

### Centerline XYZ

Whitespace-separated `x y z`, with blank lines separating closed components.

### Explicit strut sidecar (recommended when exported by the constrained solver)

CSV columns:

```text
comp_a,s_norm,comp_b,t_norm,multiplier
0,0.1042,0,0.7319,1.238e-3
```

`multiplier` is optional. `s_norm` and `t_norm` are normalized component arclengths in `[0,1)`.

### Explicit kink sidecar

```text
comp,s_norm,multiplier
0,0.4221,7.19e-4
```

When all active constraints include solver-supplied multipliers, the package performs an **independent supplied-multiplier KKT audit** in addition to the blind NNLS reconstruction.

## Private dataset manifest

Copy `examples/datasets.private.example.json` and replace the cases with your relaxed datasets. Recommended fields are:

```json
{
  "path": "C:/.../knot_3.1/..._polish.txt",
  "label": "3_1 polish N1200",
  "group": "3_1-polish-family",
  "resolution": 1200,
  "radius": 0.5,
  "source_role": "ridgerunner-polish-audit-geometry",
  "geometry_status": "near-ideal-candidate",
  "contact_sidecar": "C:/.../struts.csv",
  "kink_sidecar": "C:/.../kinks.csv",
  "complete_mechanical_model": false
}
```

Keep `complete_mechanical_model=false` for a contact-only rigidity matrix. Then `ker(A^T)` is reported as a contact-network mechanism diagnostic only; it is **not** interpreted as a complete dynamical instability of the SST knot.

## Build on Windows

From a Developer Command Prompt, or any shell with CMake and a C++17 compiler:

```bat
build_native.cmd
```

Python dependencies:

```bat
python -m pip install -r requirements.txt
```

The package has no C++ third-party dependency.

## Run a blinded campaign

```bat
python python\prepare_blind.py datasets.private.json --out blind_campaign --private-key private_blind_key.json
python python\run_blind.py blind_campaign
```

Do not put `private_blind_key.json` inside `blind_campaign`.

After all outputs are frozen:

```bat
python python\unblind.py blind_campaign\results private_blind_key.json --out unblinded_summary.json
```

## Main outputs per case

`metrics.json` reports:

- `chi_kkt` from a nonnegative NNLS reconstruction;
- local reciprocal-closure residuals;
- full singular spectrum, positive singular minimum and condition number;
- right nullity (`self-stress` dimension before positivity);
- positive-self-stress LP feasibility and a lower bound on the affine dimension of the normalized positive slice;
- raw left nullity and left nullity after subtracting global rigid modes;
- duplicate-column count;
- solver-supplied multiplier audit, if available;
- strict-reciprocity status guard;
- SST force--area coherence identity;
- physical reciprocal face areas only if a physical force scale in newtons was preregistered.

`convergence.json` compares neighboring resolutions inside each blinded group.

## Default preregistration

The provided values are deliberately fixed before the example campaign:

- SVD relative tolerance: `1e-9`;
- KKT pass/warn: `5e-3 / 1e-2`;
- local closure pass/warn: `1e-2 / 5e-2`;
- near-singular warning: \(\sigma_{\min}^{+}/\sigma_{\max}<10^{-6}\);
- inferred-contact shell: `1.5%` around the declared/inferred tube radius;
- local same-component arclength exclusion: `2%`;
- contact-map Hausdorff pass/warn: `5e-3 / 2e-2` in normalized arclength coordinates.

These are **campaign gates, not Canon constants**. For a production campaign they should be frozen from numerical-resolution requirements and control cases before unblinding the physical identities.

## Interpretation guard: Maxwell reciprocity

Maxwell's reciprocal diagrams encode force equilibrium by closed polygons in 2D and, in 3D, by face areas of a closed polyhedron. Maxwell also explicitly notes that a mechanical force problem can remain solvable when a perfect reciprocal figure cannot be constructed; redundant force diagrams can then be used. The package follows exactly that guard: failure to build or supply a strict dual complex is never by itself an SST falsification.

## Synthetic controls

`run_tests.cmd` validates:

- a known matrix with a positive self-stress;
- a known matrix without one;
- an exactly solvable NNLS equilibrium;
- the v0.8.35 numerical force--area coherence identity.

`run_example_blind.cmd` builds and runs two analytic trefoil smoke-test resolutions. These are software controls only, not physical or Ridgerunner-certified SST evidence.

## Version

`v0.1.0` is a falsifier infrastructure release. It does not claim a successful Maxwell reciprocal polyhedron for any SST knot and does not promote the factor-nine contact hypothesis.

## Convenience scan for an existing relaxed directory

A private manifest can be bootstrapped from a Ridgerunner directory:

```bat
python tools\make_private_manifest_from_relaxed.py C:\workspace\...\knots --glob "**/*polish*.txt" --radius 0.5 --out datasets.private.json
```

Review the generated grouping, resolution, radius, status, and source role **before** blinding. The scanner is convenience tooling; it is not a topology or certification authority.
