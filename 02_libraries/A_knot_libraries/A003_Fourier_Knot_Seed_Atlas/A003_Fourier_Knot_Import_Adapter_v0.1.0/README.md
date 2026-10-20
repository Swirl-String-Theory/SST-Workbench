# SST Fourier Knot Import Adapter v0.1.0

**Scientific state: DEVELOPMENT — GEOMETRIC IMPORT ONLY.** Source: `SST_Fourier_Knot_Seed_Atlas_v0.1.1` (30 analytic seeds, 240 XYZ files). No original atlas bytes or frozen Knot Library files are modified.

## Suggested placement (Windows)

```
SST-Workbench/02_libraries/A_knot_libraries/
  SST_Fourier_Knot_Seed_Atlas/v0.1.1/    [separate 240-file atlas]
  SST_Fourier_Knot_Import_Adapter/v0.1.0/ [this adapter]
  SST_Knot_Library/                      [unchanged]
```

Python >=3.10 and NumPy. No package install or network needed for validation. For actual `prepare` use installed/extracted `sst_knotlib` with explicitly matched version (Drive-reviewed 0.2.5). Newer Knot Library releases must be tested explicitly; the adapter does **not** silently claim v0.3.2 compatibility.

## Commands

From the adapter directory, substituting your real atlas path:

```bat
python fourier_atlas_adapter.py --atlas "..\..\SST_Fourier_Knot_Seed_Atlas\v0.1.1" --out outputs catalog
python fourier_atlas_adapter.py --atlas "..\..\SST_Fourier_Knot_Seed_Atlas\v0.1.1" --out outputs audit
```

`catalog` creates `outputs/fourier_external_registry.json` (external **sidecar**, not a mutation of the frozen `sst_knotlib` reference registry) and `outputs/validation_report.json`.

Before `prepare`, set the path to a tested, frozen library, for example:

```bat
set SST_KNOT_LIBRARY_HOME=C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\SST_Knot_Library\SST_Knot_Library_v0.2.5
python fourier_atlas_adapter.py --atlas "..\..\SST_Fourier_Knot_Seed_Atlas\v0.1.1" --out outputs prepare --seed torus_8_19_direct --sampling uniform_s_polyline --N 2400 --target-N 512 --core-radius 0.05 --expected-library-version 0.2.5
```

Here `--core-radius 0.05` is an **illustrative dimensionless test radius**, not SST's canonical physical `r_c`. Without `--unit-scale-m`, all coordinates and the core radius are dimensionless. To assign physical scale, **explicitly** supply `--unit-scale-m` in m/source-unit and a `--core-radius` in meters. Physical scale cannot be derived from the pure knot equations or from XYZ exports.

For a pinned installed library that lacks an `SST_KNOT_LIBRARY_HOME` override, omit the environment variable. `--topology-provider auto` uses only installed providers; no packages are silently installed. `--require-topology-certified` fails closed unless the library supplies an independent `CERTIFIED` result. The v0.2.5 KAtlas snapshot only contains `3_1`, `4_1`, `6_2`, and `7_4`, so the adapter leaves `8_19` and other outside IDs explicitly `NOT_REGISTERED` (while still preserving their **source-declared expected topology**).

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
