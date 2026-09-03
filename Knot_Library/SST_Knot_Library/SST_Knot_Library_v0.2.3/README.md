# SST Knot Library v0.2.3

A falsifier-grade umbrella library for SST knot **geometry**, **topology reference/certification**, **file interoperability**, **blind provenance**, and **pre-dynamics qualification**.

The design goal is not to trust any one knot source. A candidate moves through four separate trust layers:

```text
source bytes -> canonical geometry -> topology status -> geometry qualification -> downstream physics
```

A filename such as `6.2/ideal.txt` is treated only as **expected topology = 6_2**. It is never considered independently certified from its name.

## Bundled core

- Previous SST Knot Geometry Library v0.1.3 functionality, API-compatible through `sst_knotlib`.
- C++17/OpenMP pybind11 kernels for nonlocal clearance, writhe and linking.
- Uniform arclength resampling, normalization, Fourier smoothing.
- Bishop/rotation-minimizing frames, ribbon edges and thread bundles.
- Geometry gates: sampling uniformity, clearance/core, curvature/core and tube-embeddability proxy.
- Multi-component link support through VECT plus pairwise Gauss-linking matrices.
- Resolution-convergence reports.
- Exact geometry SHA-256 and byte-exact blind reveal commitments.
- Analytic/control families:
  - classic trefoil `3_1`;
  - anisotropic `T(p,q)` / shader-track trefoil family;
  - `S^3 -> SO(4) -> R^3` figure-eight control;
  - Knot Atlas-listed Lissajous `7_4` reference;
  - generic Artin braid-closure seed generator.

## Offline KAtlas topology registry

`sst_knotlib/data/katlas_snapshot_v1.json` is a small immutable reference snapshot for SST's currently used knot types:

- `3_1`
- `4_1`
- `6_2`
- `7_4`

Each record contains source URL, PD, Gauss, DT, minimum braid representative and selected reference invariants. The snapshot is SHA-256 verified every time it is opened.

The snapshot does **not** contain KnotTheory` source code or copied web pages. It is intentionally small and immutable; with optional pyknotid installed, arbitrary catalogue knot labels can still be geometry-certified even when they are not in this local KAtlas snapshot.

## Importers

`load_geometry()` auto-detects:

- plain XYZ / CSV (`ideal.txt`, coordinate `fseries`, KnotPlot raw ASCII);
- Brian Gilbert / Knot Atlas `<AB>/<HT>` ideal-knot Fourier records;
- multi-component `VECT` (Ridgerunner/plCurve compatible);
- KnotPlot 1.0 `LOCF` and `LOCD` binary coordinate fields.

KnotPlot `LOCS`/`LOCC` quantized fields are deliberately rejected by default. Export them to `LOCD`, `LOCF`, raw ASCII, or VECT first; a falsifier should not silently decode a lossy format with uncertain conventions.

If a file named `fseries` is not actually an XYZ coordinate series, the loader rejects it rather than guessing a Fourier-coefficient convention. Brian Gilbert `<AB>/<HT>` records are the exception because their Fourier convention is explicitly documented and decoded by a dedicated adapter. Known TwelveData summary CSV files are classified as metadata and skipped rather than parsed as centerlines.

## Optional independent providers

No third-party mathematical package is silently installed by `run_all.cmd`.

`python -m sst_knotlib providers` reports what is available:

- **pyknotid** (MIT): optional space-curve identification and invariants;
- **Spherogram** (GPLv2+): optional diagram/DT/reference cross-check;
- **SnapPy** (GPLv2+): optional hyperbolic-complement reference cross-check;
- **KnotPlot**: external executable/data source, never redistributed;
- **Ridgerunner**: external relaxer/data source, never redistributed.

This keeps the core small and avoids mixing third-party licensing into the SST package.

## Disjoint topology namespaces

Filename-derived labels cannot collide across object classes:

- knots: `6_2`;
- links: `L6_3_2`;
- torus families: `T(6,15)`.

For `T(p,q)` the expected number of components is `gcd(p,q)`. These are still only expected-topology hints for imported geometry. See `docs/TOPOLOGY_NAMESPACES.md`.

## Topology status semantics

Every prepared record has exactly one of:

- `CERTIFIED` — an independent space-curve provider matched the expected topology;
- `MISMATCH` — provider result conflicts with the expected topology;
- `UNVERIFIED` — expected topology is known but no independent geometry provider was available;
- `NOT_REGISTERED` — topology is not in the local reference snapshot;
- `ERROR` — provider failed.

`UNVERIFIED` is never promoted to `CERTIFIED` from a filename, folder name, KAtlas lookup, or geometry resemblance.

## Falsifier entry policies

`evaluate_record(record, policy=...)` provides three explicit policies:

- `strict`: geometry must pass **and** topology must be `CERTIFIED`;
- `audit` (default): `MISMATCH`/`ERROR` block; `UNVERIFIED` may continue but remains visible;
- `geometry-only`: legacy behavior.

For publication-grade final campaigns, use `strict` when an independent topology provider is available.

## Key commands

```bat
run_all.cmd
```

Full native validation, 20 smoke tests, release/source-catalog audit, registry validation, reference validation, seed suite and blind campaign.

```bat
python -m sst_knotlib registry
python -m sst_knotlib registry 6_2
python -m sst_knotlib providers
python -m sst_knotlib braid-info 7_4
```

Inspect any existing geometry:

```bat
python -m sst_knotlib inspect ..\..\KnotPlot\knots\final\6.2\ideal.txt ^
  --topology 6_2 --provider auto --core-radius 0.05 ^
  --out outputs\6_2_ideal_record.json
```

Scan the existing relaxed-knot dataset without modifying it:

```bat
run_dataset_inventory.cmd ..\..\KnotPlot\knots\final
```

With an optional space-curve provider installed:

```bat
python -m sst_knotlib scan-dataset ..\..\KnotPlot\knots\final ^
  --certify --provider pyknotid --out outputs\dataset_inventory_certified.json
```

Generate an independent seed from KAtlas topology rather than from `ideal.txt`/KnotPlot/Ridgerunner:

```bat
python -m sst_knotlib seed-from-topology 6_2 --method braid --out outputs\6_2_katlas_braid.xyz
python -m sst_knotlib seed-from-topology 7_4 --method lissajous --out outputs\7_4_lissajous.xyz
```

## Downstream API

```python
import sst_knotlib as sk

asset = sk.load_geometry('6.2/ideal.txt')
points, provenance = sk.prepare_for_falsifier(
    asset.points,
    core_radius=0.05,
    n=512,
    expected_topology='6_2',
    topology_provider='auto',
)
```

To hard-stop on unverified topology:

```python
points, provenance = sk.prepare_for_falsifier(
    asset.points,
    core_radius=0.05,
    expected_topology='6_2',
    require_topology_certified=True,
)
```

## Scientific boundary

KAtlas/Spherogram/pyknotid answer topological questions. `ideal.txt`, KnotPlot and Ridgerunner supply embeddings. Geometry qualification checks numerical suitability. None of these establishes Euler/Biot-Savart stability; that remains the job of the downstream SST falsifiers.

See `docs/SAFETY_AND_TRUST_MODEL.md`, `docs/PROVIDER_MATRIX.md`, `docs/TOPOLOGY_NAMESPACES.md`, `docs/V0.2.0_OUTPUT_AUDIT.md`, and `docs/FALSIFIER_INTEGRATION_V0.2.md`.

## v0.2.3 broad-project scanner behavior

Whole project trees often contain documentation, logs and CSV/text metadata next to knot data. The
scanner now separates `OK`, `SKIPPED_METADATA`, `SKIPPED_NON_GEOMETRY` and real `ERROR` records.
It also reports `discovered_file_count` and `ignored_extension_counts`, so a dataset such as an unknown
Fourier-series archive can be onboarded without guessing its format. Repeated
`run_dataset_inventory.cmd` calls are preserved under `outputs\dataset_inventories\` instead of silently
overwriting the only audit record. See `docs/DATASET_SCANNER_TRUST.md`.
