# SST Knot Library v0.2.1

A falsifier-grade umbrella library for SST knot **geometry**, **topology reference/certification**, **file interoperability**, **blind provenance**, and **pre-dynamics qualification**.

The design goal is not to trust any one knot source. A candidate moves through four separate trust layers:

```text
source bytes -> canonical geometry -> topology status -> geometry qualification -> downstream physics
```

A filename such as `6.2/ideal.txt` is treated only as **expected topology = 6_2**. It is never considered independently certified from its name.

As of v0.2.1 the library is native to the Workbench `Knot_Library/` layout. Geometry under `Sources/<Provider>/` carries a machine `provider_id` from that provider's `SOURCE.json` (directory names are never parsed as identity).

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
- multi-component `VECT` (Ridgerunner/plCurve compatible);
- KnotPlot 1.0 `LOCF` and `LOCD` binary coordinate fields.

KnotPlot `LOCS`/`LOCC` quantized fields are deliberately rejected by default. Export them to `LOCD`, `LOCF`, raw ASCII, or VECT first; a falsifier should not silently decode a lossy format with uncertain conventions.

If a file named `fseries` is not actually an XYZ coordinate series, the loader rejects it rather than guessing a Fourier-coefficient convention.

Under `Knot_Library/Sources/`, `provider_id` comes from `SOURCE.json`. Path heuristics are fallbacks only for files outside Sources (and never certify topology).

## Optional independent providers

No third-party mathematical package is silently installed by `run_all.cmd`.

`python -m sst_knotlib providers` reports what is available:

- **pyknotid** (MIT): optional space-curve identification and invariants;
- **Spherogram** (GPLv2+): optional diagram/DT/reference cross-check;
- **SnapPy** (GPLv2+): optional hyperbolic-complement reference cross-check;
- **KnotPlot**: external executable/data source, never redistributed;
- **Ridgerunner**: external relaxer/data source, never redistributed.

This keeps the core small and avoids mixing third-party licensing into the SST package.

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

- `strict`: geometry must pass, topology must be `CERTIFIED`, and `provider_id` must be known;
- `audit` (default): `MISMATCH`/`ERROR` block; `UNVERIFIED` may continue but remains visible;
- `geometry-only`: legacy behavior.

For publication-grade final campaigns, use `strict` when an independent topology provider is available.

## Key commands

```bat
run_all.cmd
```

Full native validation, smoke tests, registry audit, reference validation, seed suite and blind campaign.

```bat
python -m sst_knotlib registry
python -m sst_knotlib registry 6_2
python -m sst_knotlib providers
python -m sst_knotlib braid-info 7_4
```

Inspect geometry under the provenance layout:

```bat
python -m sst_knotlib inspect ^
  ..\..\Sources\FourierSeries_Fremlin\extracted\6_2\knot.6_2.short ^
  --topology 6_2 --provider auto --core-radius 0.05 ^
  --out outputs\6_2_fremlin_record.json
```

Scan `Knot_Library/Sources` (default) or an explicit root:

```bat
run_dataset_inventory.cmd
python -m sst_knotlib scan-dataset --out outputs\dataset_inventory.json
```

Inventory legacy Workbench paths without moving anything:

```bat
run_inventory.cmd
python -m sst_knotlib inventory-sources --require-no-move
```

Generate an independent seed from KAtlas topology rather than from `ideal.txt`/KnotPlot/Ridgerunner:

```bat
python -m sst_knotlib seed-from-topology 6_2 --method braid --out outputs\6_2_katlas_braid.xyz
python -m sst_knotlib seed-from-topology 7_4 --method lissajous --out outputs\7_4_lissajous.xyz
```

## Downstream API

```python
import sst_knotlib as sk

asset = sk.load_geometry(r'..\..\Sources\FourierSeries_Fremlin\extracted\6_2\knot.6_2.short')
# asset.provider_id == 'fremlin_fourier'
comps, record = sk.make_knot_record(asset.source_path, expected_topology='6_2', core_radius=0.05)
sk.evaluate_record(record.to_dict(), policy='audit')
```

See `docs/PROVIDER_MATRIX.md` and the parent `Knot_Library/README.md` for the provenance directory map.
