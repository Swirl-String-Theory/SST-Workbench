# PKLSA Universal Atlas Adapter v0.1.0

**Scope:** additive, read-only, fail-closed bridge from **E010 v0.4.0** to current and future SST-Workbench falsifiers. Does not change E010, B007, A006, A011, A054, A065, VortexLab, active defaults, registry/catalog IDs, or scheduled jobs.

## Scientific contract

- E010's current atlas is **intake-qualified only**. `scientific=NOT_RUN`, and all 54,450 planned dynamics scenarios remain `NOT_RUN` in E010.
- Historical `PASS`/`FAIL` labels are **retained historical qualifications**; neither implies physical validity or dynamic stability. Historical records default to visible, but a consumer must still qualify them for its own purpose.
- The contained Ruban v0.3.6 geometry domain is **B0 = 0.02 through 0.32**, with 121 values per family. Later B007-generated minima at B0 > 0.32 are **not** stored as E010 v0.4.0 atlas records. Generate those explicitly in B007 and register any resulting geometry separately; never fabricate atlas IDs.
- The 7,260 Ruban variants are from **one analytic source group**, not independent scientific providers. Their `research_only=True` blocks selection/load unless `--allow-research` is explicit.
- `topology_id`, `parametric_embedding`, and `source_provider` are distinct. `T_2_5` is the torus knot `5_1`, **not** the twist knot `5_2`.
- Reader validates original raw SHA-256, component counts and parsed float64 geometry SHA-256. An interpolated 4096-point polygon does not add independent geometry information or prove isotopy.
- No automatically calibrated meters, core radius, finite-core reach, Euler equilibrium, or stability claims. Optional `--scale` is *just a numerical coordinate multiplier*, never an SI calibration.
- Archive and index are pinned to the supplied E010 v0.4.0 publication; **future atlas versions require a new adapter release or explicit code/pin review**.

## Installation (Windows 11)

Recommended location **only after checking the live family catalog**:

```
C:\workspace\projects\SST-Workbench\04_tools\A_geometry\PKLSA_Universal_Atlas_Adapter_v0.1.0\
```

No catalog ID is invented or existing registration changed. Extract **this adapter release only** to that directory; use the already published E010 atlas in place. Python 3.14 and NumPy are recommended, matching the E010 environment.

```bat
py -3.14 -m pip install -r requirements.txt
rem Optional: install as a reusable package across falsifiers
py -3.14 -m pip install -e .
```

Set one path to your existing payload ZIP or its extracted contents:

```bat
set "E010_ATLAS=C:\workspace\projects\SST-Workbench\01_research\E_pipelines\E010_pklsa_parametric_knot_link_seed_atlas\E010-v0.4.0\SST_Parametric_Knot_Link_Seed_Atlas_v0.4.0_outputs.zip"
```

**Adjust the path to match where your ZIP actually resides**. `E010_ATLAS` may instead point to the extracted folder that directly contains `COMBINED_INDEX.json`. The bridge never expands the entire 1 GiB atlas on disk: ZIP input materializes only the index, original Python readers, and selected source files temporarily. There is no need to duplicate the mega-atlas into the adapter folder.

## Recommended command order

**G0 — Verify only the pinned publication and upstream reader:**

```bat
run_all.cmd VERIFY
run_all.cmd SELFTEST
```

The default verification checks the full index pin and reader schema; it **does not rerun the full 52,596-file E010 verification** that you already completed. `selftest` includes integration tests using the given `E010_ATLAS` path.

**G1 — Discover candidate records (no geometry generation):**

```bat
run_all.cmd select --topology 3_1 --collection historical_v031 --limit 15
run_all.cmd select --topology 5_2 --collection historical_v031 --limit 15
run_all.cmd select --embedding T_2_3 --variant nominal --b0-min 0.28 --b0-max 0.32 --allow-research --limit 15
run_all.cmd select --embedding T_3_9 --variant nominal --allow-research --components 3 --limit 10
```

Note: selecting `T_2_3` without `--allow-research` gives **zero** matching IDs; this is intentional.

**G2 — One small, version-locked B007 intake dataset:**

First obtain the exact record IDs with `select`, then export a **create-only** dataset using those IDs:

```bat
run_all.cmd export --id RUBAN_v036_T_2_3_B0200_N1024_nominal --allow-research --consumer B007-v0.2.3-intake --output "..\B007_ATLAS_T23_PILOT"
run_all.cmd verify-dataset "..\B007_ATLAS_T23_PILOT"
```

**G3 — One three-component torus link** (use `select` to obtain its exact ID before export):

```bat
run_all.cmd select --embedding T_3_6 --variant nominal --allow-research --limit 5
run_all.cmd export --embedding T_3_6 --variant nominal --b0-min 0.20 --b0-max 0.20 --allow-research --consumer B007-v0.2.3-link-control --output "..\B007_ATLAS_T36_PILOT"
```

**G4 — Fair cross-embedding comparison:** make **separate** dataset exports with historical `3_1` carriers from different `--provider` or `--source-group` groups. Record identical normalizations and independent spatial/temporal convergence in the *falsifier*, not in the atlas. Do **not** merge copies from one analytic source group as independent physical evidence.

## Additional commands / safety

```bat
run_all.cmd export --topology 3_1 --collection historical_v031 --historical-status PASS --limit 5 --consumer A006-geometric-control --output "..\A006_ATLAS_3_1_5"
run_all.cmd export --embedding T_2_3 --variant nominal --allow-research --limit 1 --resample 4096 --consumer B007-interpolation-diagnostic --output "..\B007_ATLAS_INTERPOLATED_4096"
run_all.cmd select --topology 6_1 --collection historical_v031 --limit 10
```

- `--limit N` is only an **explicit truncation** on `export`. Without it, export refuses more than `--max-records 100` instead of silently truncating the dataset.
- Export refuses an existing destination; it will never overwrite a previous falsifier selection, atlas file or existing output folder. Every exported `DATASET_MANIFEST.json` includes source ID, ordered components, source and export hashes, source independent group, topology label, original scientific status, and any interpolation/scaling.
- Exported XYZ files are named `seeds/<record_id>/component_000.xyz`, etc. Each component is separate. `DATASET_MANIFEST.json.sha256` and `verify-dataset` verify exported payloads.
- `--unique-geometry` only collapses exactly equal ordered float64 geometry hashes for *selection*, not topology or equivalence under rotation, resampling or isotopy. The full atlas is preserved.
- `--scale` does not declare physical dimensions. If a consumer needs meters, it must supply its own externally validated length calibration **with a separate gate**.
- For ZIP input, the Python reader runs from the *original E010 package contained in the ZIP*. E010 is trusted project code, not fetched from any website; the external ZIP digest is pinned before any code is loaded.

## Portable consumer reader (B007 / A006 / VortexLab)

An existing consumer only needs this small adapter package and the **exported dataset directory**; it need not mount the 1 GiB atlas or import E010 code:

```python
from pklsa_bridge import ConsumerDataset

source = ConsumerDataset(r'C:\path\to\B007_ATLAS_T36_PILOT')
for identity in source.list_ids():
    components = source.load(identity)   # ordered, hash-verified Nx3 arrays
    metadata = source.metadata(identity) # original topology / geometry ID / provider
    # Pass components to the consumer's existing geometry entry point.
```

The installed B007 v0.2.2 CLI is **not modified** by this release. Connecting its internal screening pipeline to this contract remains a separate, explicit B007 version patch.

## Python API (other falsifiers)

```python
from pklsa_bridge import AtlasBridge

with AtlasBridge(r'C:\path\to\SST_Parametric_Knot_Link_Seed_Atlas_v0.4.0_outputs.zip') as bridge:
    ids = bridge.query(topology='3_1', collection='historical_v031', limit=5)
    for identity in ids:
        parts = bridge.load(identity)          # list of independent Nx3 components
        source = bridge.source_summary(identity)
    ruban = bridge.query(embedding='T_3_6', variant='nominal', allow_research=True, limit=1)
    components = bridge.load(ruban[0], allow_research=True)  # 3 components
```

**Integration rule:** existing falsifier should import `pklsa_bridge` or use the versioned exported dataset manifest. Do not copy E010 data into each old falsifier; do not automatically switch historical runs to v0.4.0. A consumer must explicitly opt in to new dataset-selection and qualify physics independently.

## Known exclusions in v0.1.0

- Not an automatic geometry optimizer, native higher-resolution torus generator, dynamic solver, or topology certifier.
- Does not independently recognize Borromean topology; the four custom imported B007 candidates must be separately registered in their existing dataset source. Only records **present in E010** are selectable here.
- Does not modify or invoke `run_all.cmd` inside B007, A006 or other falsifiers. The adapter is a stable input contract for an explicit future consumer patch.
- Does not run independent spectral finite-core convergence, Milnor invariants, Floquet modes, equilibrium continuation or scenario scheduling.
- Does not currently assign an SST-Workbench catalog ID: current `family_hierarchy.json` and `catalog_index.json` should be checked before registration.

## Source files and test coverage

- `pklsa_bridge/adapter.py`: source reader orchestration, metadata query, create-only export, readback checks, and manifest verification.
- `pklsa_bridge/cli.py`: stable argument interface.
- `pklsa_bridge/consumer.py`: tiny export reader, integrity-checked without the full E010 source archive.
- `tests/test_bridge.py`: read-only integration and failure tests with original E010 v0.4.0 ZIP.
- `examples/consumer_python.py`: direct Python integration example for current and future falsifiers.
- `project.json`: additive tool metadata, catalog registration deferred.
- `pyproject.toml`: optional editable installation, explicit package discovery to prevent setuptools flat-layout collisions.

Scientific status: `RESEARCH_DATASET_BRIDGE_ONLY`, **not** an Euler equilibrium or qualification result.
