# SST Fermat pybind research v0.2.0

Standalone Python + C++17/pybind11 research harness. It does **not** import or modify SSTcore.

## Scope added in v0.2.0

The same local transverse Fermat diagnostic is now applied from the start to four uploaded ideal-knot centerlines:

| Knot | Catalog source ID | Role in the comparison | Fourier modes |
|---|---:|---|---:|
| `0_1` | `0:1:1` | unknotted circular control | 1 |
| `3_1` | `3:1:1` | trefoil, first non-trivial chiral knot | 183 |
| `4_1` | `4:1:1` | achiral figure-eight control | 220 |
| `5_2` | `5:1:2` | chiral twist-knot comparison | 241 |

The coefficients are extracted from the uploaded `ideal_favorites.txt` database and bundled in `fermat_ext/data/ideal_knots_subset.json`. The source convention is

\[
\boldsymbol\gamma(t)
=
\sum_i\left[\mathbf A_i\cos(it)+\mathbf B_i\sin(it)\right],
\qquad 0\le t<2\pi.
\]

The curves are uniformly resampled in arclength before the Biot--Savart calculation. Their source normalization has `D=1`; `--scale-over-rc` applies only a uniform coordinate scale and does not identify `D` with a physical SST core diameter.

## Scientific status

The implemented scan evaluates the regularized filament field at probes in transported normal planes and searches for local minima of

\[
R_F(\rho;s,\theta)
=
\frac{\rho}{\sqrt{1-\lVert\boldsymbol\beta\rVert^2}},
\qquad
\boldsymbol\beta=\frac{\mathbf u}{c}.
\]

Every detected minimum is labelled only

```text
LOCAL_TRANSVERSE_MINIMUM_CANDIDATE
```

It is **not** a certification of a global closed Fermat geodesic, light ring, or QSM pole. All JSON outputs retain:

```json
"global_closed_orbit_certified": false,
"qsm_certified": false
```

## Build the native extension

From the project root in the activated virtual environment:

```bat
python -m pip install -r requirements.txt
python -m fermat_ext.build_ext_if_needed --force --strict
```

A successful Windows/Python 3.14 build typically creates:

```text
fermat_ext\_fermat_native.cp314-win_amd64.pyd
```

## Run all four knots

### Fast audit preset

```bat
python run_knot_matrix.py --preset smoke --out-dir knot_matrix_smoke
```

### Standard comparison

```bat
python run_knot_matrix.py --preset standard --out-dir knot_matrix_standard
```

### High-resolution comparison

```bat
python run_knot_matrix.py --preset high --out-dir knot_matrix_high
```

The matrix runner evaluates both the native C++ backend and the independent Python fallback, then reports the maximum componentwise field discrepancy for each knot.

Expected native status:

```json
"native_available_for_all_knots": true,
"native_python_parity_certified_for_all_knots": true
```

## Scan one knot

```bat
python run_knot_scan.py --knot-id 0_1 --summary-only
python run_knot_scan.py --knot-id 3_1 --summary-only
python run_knot_scan.py --knot-id 4_1 --summary-only
python run_knot_scan.py --knot-id 5_2 --summary-only
```

The old generated torus parametrization remains available only as a comparison route:

```bat
python run_knot_scan.py --generated-torus --p 2 --q 3 --summary-only
```

## Full audit battery

```bat
python run_all_checks.py --out-dir audit_out_native --require-native
```

This validates:

- the analytic external-profile critical radius;
- Python/C++ radial-profile parity;
- Python/C++ Rankine-sweep parity;
- exact presence of `0_1`, `3_1`, `4_1`, and `5_2`;
- reconstruction of the uploaded source lengths;
- native/Python Biot--Savart parity for all four knots;
- preservation of the epistemic guards.

Use `--no-auto-build` only after the `.pyd` has already been built:

```bat
python run_all_checks.py --out-dir audit_out_native --no-auto-build --require-native
```

## Resolution presets

| Preset | Centerline | Stations | Angles | Radial samples | Probes per knot |
|---|---:|---:|---:|---:|---:|
| `smoke` | 128 | 4 | 8 | 48 | 1,536 |
| `standard` | 512 | 16 | 24 | 160 | 61,440 |
| `high` | 1024 | 32 | 48 | 320 | 491,520 |

The high preset is computationally substantial because every probe is evaluated against every centerline segment.

## Output files

`run_knot_matrix.py` writes:

```text
knot_matrix.json
knot_matrix.csv
0_1_primary.json / 0_1_python.json
3_1_primary.json / 3_1_python.json
4_1_primary.json / 4_1_python.json
5_2_primary.json / 5_2_python.json
```

The principal cross-knot observables available in v0.2.0 are:

- local candidate count and locations;
- invalid-clock probe count;
- minimum, maximum, mean and RMS \(\lVert\boldsymbol\beta\rVert\);
- transported-frame closure mismatch diagnostic;
- source-length reconstruction error;
- native/Python field parity.

## Next research gate

The next non-local stage is a Hamiltonian Fermat-geodesic shooting solver with monodromy/Floquet analysis. The current local normal-plane scan is deliberately retained as a cheaper precursor and regression test.
