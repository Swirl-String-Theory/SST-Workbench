# SST Fourier Knot Import Adapter v0.1.1

**Scientific state: DEVELOPMENT — GEOMETRIC IMPORT ONLY.** Source: `SST_Fourier_Knot_Seed_Atlas_v0.1.1` (30 analytic seeds, 240 XYZ files). No original atlas bytes or frozen Knot Library files are modified.

## Absolute placement (Windows, A003)

```text
C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\
  A003_Fourier_Knot_Seed_Atlas\
    A003-v0.1.1\                         # original pinned atlas, unchanged
    A003_Fourier_Knot_Import_Adapter_v0.1.1\  # this patched adapter
```

Use a new versioned adapter directory to preserve v0.1.0. Python >=3.10 and NumPy; no network required for the standalone audit. The A003 seed atlas remains the independent source of truth and must not be repackaged or rehashed.

## Run instructions (no manual path editing)

From the new adapter directory, run:

```bat
run_all.cmd
```

Or directly:

```bat
python fourier_atlas_adapter.py --out outputs catalog
python fourier_atlas_adapter.py --out outputs audit
```

The patched Python module automatically locates the adjacent `..\A003-v0.1.1`.
Resolution priority is **explicit `--atlas` / `--atlas-root`**, then environment variable `SST_ATLAS_ROOT`, then the adjacent directory. An explicitly selected but invalid path fails closed; it will *not* silently fall back to another atlas. For a nonstandard location:

```bat
run_all.cmd "D:\Datasets\A003-v0.1.1"
python fourier_atlas_adapter.py --atlas-root "D:\Datasets\A003-v0.1.1" --out outputs catalog
```

`catalog` produces `outputs/fourier_external_registry.json` and `outputs/validation_report.json`, both sidecars. Source data and the canonical Workbench catalog remain untouched.

## Optional real SST Knot Library integration

Before running `prepare`, point to an installed, tested, *pinned* Knot Library. Example for the Drive-reviewed v0.2.5 contract:

```bat
set "SST_KNOT_LIBRARY_HOME=C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\SST_Knot_Library\SST_Knot_Library_v0.2.5"
python fourier_atlas_adapter.py --out outputs prepare --seed torus_8_19_direct --sampling uniform_s_polyline --N 2400 --target-N 512 --core-radius 0.05 --expected-library-version 0.2.5
```

The library `0.2.5` path above is an illustrative location; verify where you actually installed it. The `0.3.2` runtime and later builds have not been tested against this adapter. The dimensionless `--core-radius 0.05` is an example only, **not** physical `r_c`. To supply physical units, you must explicitly use a `--unit-scale-m` (m/source unit) and pass `--core-radius` in meters; the adapter never infers this from geometry.

Strict independent topology certification, complete PKLSA dynamics and physical stability are **not** demonstrated by this patch.

## Gates

- `G0_MANIFEST_SCHEMA`: version, profile, record uniqueness, seed metadata, exact schema **and a pinned source manifest SHA-256**.
- `G1_HASH_AND_XYZ`: SHA-256 of all 240 assets, XYZ dimensionality, finite values, nonzero cyclic segments, sampling profile.
- `G2_GEOMETRIC_MIRROR_DIAGNOSTIC`: representative generic-projection signed crossing sum reverses under reflection in the projection plane. This is a *chirality regression diagnostic*, **not** independently proven trefoil/twist/torus knot identity. Declared chirality and mirror conventions remain not certified.
- `G3_SAMPLING_CONVERGENCE`: for each seed/mode, BASIC 1200→2400 and FULL 4800→9600 plus 2400→4800 bridge; registered relative RMS and polygonal perimeter deltas. Thresholds are numerical integrity screens, not PKLSA convergence certificates. The current source atlas has 20 polygon-chord warning entries (maximum chord-length ratio about 3.00) despite arclength reparameterization; no source file is altered.
- `G4_PHYSICAL_SCALE`: intentionally `NOT_DEFINED`.
- `G5_INDEPENDENT_TOPOLOGY`, `G6_PKLSA_EULER`: intentionally `NOT_RUN`; no physical claims.

The adapter leaves the 240 original source files, `manifest.json`, `catalog_index.json`, `family_hierarchy.json`, the frozen Knot Library and source-catalog hashes untouched. The sidecar references original source hashes and paths, preventing an ad hoc filename from masquerading as verified topology.

## Requirements and limits

- `python -m pip install numpy`
- `python -m unittest discover -s tests -v` for regression tests.
- The source manifest's signed chirality for most seeds is unresolved; a reflected geometry is a different handed version. Vertex order reversal changes circulation orientation but **does not** mirror a knot.
- The image/diagram crossing statistic is projection-dependent and is **not** a topological knot invariant. Independent topology providers and numerical ambient-isotopy gates are still required for publication-grade claims.
- Library native `prepare_for_falsifier()` is **not run** in the standalone CI unless a pinned SST Knot Library is available. A contract stub test does not replace that integration test.
- `catalog` is intentionally an external registry: do not overwrite the Workbench's canonical indexes or call imported sources `CERTIFIED` automatically.

## Data contract

`fourier_external_registry.json`: immutable identity fields `adapter_version`, `atlas_manifest_sha256`, per-entry source `sha256`, `id`, `knot`, `profile`, `sampling`, `points`, and unverified scientific statuses. Relative XYZ paths are resolved against the unpacked atlas root supplied at runtime.

`prepare`: produces `<seed>_<sampling>_N<N>_preparedN<M>.npz` with `xyz` float64 `[M,3]` (canonical resampled through `sst_knotlib`) and a matching `.json` with exact source and prepared bytes attestation plus library-returned provenance. Output files are write-once unless deliberately moved/renamed.

## Literature / basis

Kauffman (1997), *Fourier Knots*, arXiv:q-alg/9711013; Hoste (2009), *Torus Knots Are Fourier-(1,1,2) Knots*, DOI:10.1142/S0218216509006926; Boocher et al. (2009), *Sampling Lissajous and Fourier Knots*, DOI:10.1080/10586458.2009.10129057; Hoste and Zirbel (2007), *Lissajous Knots and Knots with Lissajous Projections*, DOI:10.24546/E0034450.
