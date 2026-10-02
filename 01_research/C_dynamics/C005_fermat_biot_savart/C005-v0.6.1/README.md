# SST Fermat pybind research v0.6.1

Standalone Python + C++17/pybind11 Research-Track harness. It does not import or modify SSTcore.

## Purpose

v0.6.1 extends the v0.6.0 axial hole-bundle experiment over the requested domain

\[
0.06125\leq \frac{R_b}{R_{\rm hole}}\leq 8,
\qquad
-8\leq \frac{\Gamma_h}{\Gamma_0}\leq 8.
\]

The model remains a smooth coaxial central-flux plus opposite-return-flux field in a periodic axial cell. It is radially compact and divergence-free within that model. It is not yet a finite closed racetrack or toroidal vortex bundle in unbounded space.

## Primary scientific correction

v0.6.0 ranked candidates by the relative residual

\[
\epsilon_{\rm rel}
=
\frac{\|u-u_{\rm rigid}\|}{\|u\|}.
\]

That quantity can decrease merely because a large nearly rigid velocity is added. v0.6.1 therefore uses the absolute post-fit residual norm as the primary comparison:

\[
\mathcal G_{\rm abs}
=
1-
\frac{\|u_{\rm knot}+u_{\rm bundle}-u_{\rm rigid}^{\rm best}\|}
     {\|u_{\rm knot}-u_{\rm rigid,0}^{\rm best}\|}.
\]

A candidate is marked `stabilizing=true` only when \(\mathcal G_{\rm abs}>0\). The former relative gain is retained as `relative_bundle_gain` for diagnosis. Cases that improve only the relative score are explicitly labeled `relative_only_stabilizing=true`.

## Default full grid

The full campaign uses:

- 33 logarithmically generated radius samples plus canonical anchors, producing 42 unique radius values;
- circulation step \(0.25\) over \([-8,8]\), producing 65 values;
- 2730 radius/circulation combinations;
- an exact \(\Gamma_h=0\) control at every radius;
- \(N=8192\) centerline points for the primary sweep.

The exact endpoints `0.06125`, `8`, `-8`, and `8` are always included.

## New v0.6.1 stages

1. **Full-range sweep** — evaluates all requested parameter combinations and writes JSON + CSV.
2. **Selected convergence audit** — reevaluates diverse leading candidates on a centerline ladder.
3. **Axis robustness audit** — tests offsets and tilts of the bundle axis.
4. **Residual mode projection** — reports which centerline Fourier components are reduced or amplified.
5. **Integrated manifest** — records every command, return code, log checksum, output checksum, and archive checksum.

The expensive knot field at the finest resolution is cached once and reused by later stages.

## Launchers

Native smoke test:

```bat
START_V061_HOLE_BUNDLE_SMOKE.bat
```

Portable Python-fallback smoke test:

```bat
START_V061_HOLE_BUNDLE_PYTHON_SMOKE.bat
```

Full native campaign:

```bat
START_V061_HOLE_BUNDLE_FULL_CAMPAIGN.bat
```

Resume an interrupted full campaign:

```bat
START_V061_HOLE_BUNDLE_FULL_RESUME.bat
```

The full campaign creates:

```text
v0.6.1_campaign_output/
├── 01_hole_bundle_sweep/
├── 02_selected_convergence/
├── 03_axis_robustness/
├── 04_mode_projection/
├── logs/
├── campaign_summary.json
└── campaign_manifest.json
```

and archives it as:

```text
SST_fermat_pybind_research_v0.6.1_results.zip
SST_fermat_pybind_research_v0.6.1_results.zip.sha256
```

## Direct full-range sweep

```bat
py -3 run_hole_bundle_sweep.py ^
  --knot 3_1 ^
  --epsilon 0.0019 ^
  --centerline-points 8192 ^
  --radius-min 0.06125 ^
  --radius-max 8 ^
  --radius-count 33 ^
  --radius-spacing log ^
  --circulation-min -8 ^
  --circulation-max 8 ^
  --circulation-step 0.25 ^
  --require-native ^
  --out-dir v0.6.1_hole_bundle_sweep_output
```

Explicit lists remain supported through `--radius-ratios` and `--circulation-ratios`.

## Output interpretation

Important fields in `hole_bundle_sweep.json`:

- `absolute_shape_gain`: primary stabilization score;
- `absolute_shape_energy_gain`: squared-residual energy reduction;
- `relative_bundle_gain`: legacy relative score;
- `clock_valid_on_centerline`: checks \(\max|\beta|<1\) on the sampled centerline;
- `parameter_box_boundary`: indicates that the optimum lies on a requested range boundary;
- `best_requires_range_extension`: true when the best candidate is boundary-censored.

A successful campaign means the computations and audits completed. It does not imply a physical relative equilibrium.

## Epistemic guard

All v0.6.1 outputs remain:

```text
RESEARCH_TRACK
physical_finite_closed_bundle_certified = false
global_closed_orbit_certified = false
monodromy_certified = false
qsm_certified = false
```

The Fourier indices are diagnostics along the sampled centerline; they are not yet eigenmodes of a coupled finite-core dynamical operator.

## Validation

The package includes:

- Python regression tests for v0.3–v0.6.1;
- analytic bundle-Jacobian finite-difference checks;
- exact rigid-motion projection tests;
- full-range grid endpoint/control tests;
- a Python-fallback four-stage smoke campaign;
- a standalone C++17 kernel test.

See `BUILD_VALIDATION.txt` and `validation_samples/`.
