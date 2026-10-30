# E010 Ruban T(2,3) perturbed — 2048/4096 analytic resolution export v0.1.0

**Purpose:** Prepare all **121** research-only, volume-preserving-perturbed Ruban `T_2_3` geometries from **E010 v0.4.0** at two true analytic sampling resolutions, **2048** and **4096** vertices per closed knot. This is an input-dataset export, not a dynamical calculation.

## Coverage

- One `T_2_3` knot per `B0` value: **0.0200, 0.0225, ..., 0.3200** (121 values).
- `variant=perturbed` **only**. Nominal sources are referenced by `parent_id` but not copied.
- One component per geometry, one `.xyz` file per record per resolution: **242 geometry files** in total.
- All 121 source records were loaded through the **PKLSA Universal Atlas Adapter v0.1.0** from the pinned E010 v0.4.0 portable atlas. The original **1024-point analytic formula was checked for exact float64 agreement for all 121 source coordinates**.
- Exports **re-evaluate the original analytic formula** and the same smooth, globally volume-preserving deformation at `N=2048` and `N=4096`. No interpolation of the 1024-point polygon is used. The original 1024 vertices occur exactly as nested samples in both exports.
- Higher sampling density is **not an independent source provider**, a certified isotopy check, a physical continuum reach certificate, a finite-core qualification, or proof of stable Euler dynamics.
- `R0=1` dimensionless coordinates; `B0=r0/R0` is the torus minor/major radius ratio, **not** the physical vortex-core radius. `Lambda` and `delta_over_R0` are not geometry fields and have not been evolved.

**Crucial limitation for previous B007 analysis:** this atlas spans `B0 <= 0.32`. B007 candidate minima at `B0=0.36 ... 0.40` were generated later by the B007 generator and are **not** included. Compare matching `B0` values across source and resolution; do not silently treat out-of-range candidates as present.

## Contents

Separate archives:

- `E010_T23_PERTURBED_N2048_v0.1.0_dataset.zip`: 121 closed curves and a verified `DATASET_MANIFEST.json`.
- `E010_T23_PERTURBED_N4096_v0.1.0_dataset.zip`: the corresponding 121 curves and independent dataset manifest.
- `E010_T23_PERTURBED_HIRES_v0.1.0_SOURCE.zip`: exact original E010 generator/config snapshot and an executable reconstruction script.

Audit:

- `REGENERATION_AUDIT.json`: selected family, source replay verification, resolutions, manifest checks and scientific status.
- `CROSS_RESOLUTION_AUDIT.csv`: one row per `(B0,N)`, with original record ID/hash, output XYZ hash, original/export polygon lengths, and anchor-coordinate agreement.

Both `N2048` and `N4096` folders obey `SST-ATLAS-CONSUMER-DATASET-1`, allowing integrity-only reading with the existing `pklsa_bridge.ConsumerDataset`. The generator is an additive source-frozen extension; it did not modify the original E010 archive, its index or the existing adapter.

## Regenerate on Windows

Required: Python 3.10+ with NumPy; unpacked **PKLSA Universal Atlas Adapter v0.1.0** with its dependencies; E010 v0.4.0 portable ZIP or extracted payload.

```bat
set "E010_ATLAS=C:\workspace\projects\SST-Workbench\01_research\E_pipelines\E010_pklsa_parametric_knot_link_seed_atlas\E010-v0.4.0\SST_Parametric_Knot_Link_Seed_Atlas_v0.4.0_outputs.zip"
set "PKLSA_ADAPTER=C:\path\to\PKLSA_Universal_Atlas_Adapter_v0.1.0"
run_all.cmd
```

Adjust both paths to your actual files. The script **refuses an existing destination**; don't overwrite this verified output. The source `make_dataset.py` accepts `--output` explicitly to make an independent new run.

### Verify after extraction

From the installed adapter directory:

```bat
run_all.cmd verify-dataset "C:\path\to\N2048"
run_all.cmd verify-dataset "C:\path\to\N4096"
```

Or in Python:

```python
from pklsa_bridge import ConsumerDataset
for n in (2048, 4096):
    ds = ConsumerDataset(rf'C:\path\to\N{n}')
    assert len(ds.list_ids()) == 121
    record_id = 'RUBAN_v036_T_2_3_B3200_N1024_perturbed'
    x = ds.load(record_id)[0]
    assert x.shape == (n, 3)
```

The ID deliberately retains the **original atlas record identity** `N1024`. The exported resolution is separately and unambiguously recorded in `exported_point_count` and `transforms`. This prevents treating a new re-evaluation as a previously indexed E010 record.

## B007 use

1. Use B007 v0.2.2 for independent filament-model and frame-fit qualification, **once a consumer-facing dataset input has been explicitly integrated**. B007 v0.2.2 does not natively accept `DATASET_MANIFEST.json`, so the new datasets are not yet automatically executable with `run_all.cmd`.
2. Match identical `B0`, circulation normalization, fit mode, `Lambda`, physical final time, timestep sequence and perturbation protocol when comparing 2048 and 4096 point curves.
3. Evaluate the `B0 <= 0.32` sector first. For `B0>0.32` extend the **analytic producer** explicitly under a new, clearly identified campaign; don't attribute those geometries to E010 v0.4.0.
4. Assess both spatial and temporal convergence and keep initial residual separate from long-time deformation/growth. No dynamic stability is inferred from the present geometry-only dataset.

## Provenance and status

- Atlas index SHA-256: `70af49e67406e26187607eef5c624a88989e8fd5938d0c6f42ba3b2d23b75341`.
- Atlas ZIP SHA-256: `2051ad2e9a0b51857197e6688b09d9be48bd562c01ec0e7613eddfebeb174d82`.
- Frozen original Ruban generator SHA-256: `2c73d35fd58c9f4bcb4ddbb336021883d0bdff44051105750a68fa0fc6a0c609`.
- Frozen original generator config SHA-256: `c7b29996e665296a99c376be044c66eb0ebefe31ecd516a3e53e9b908679890d`.
- Scientific admission: `NOT_GRANTED`.
- Dynamic simulations: `NOT_RUN`.
