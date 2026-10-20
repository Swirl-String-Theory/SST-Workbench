# A065-v0.3.9: A003 Fourier geometry and SST Falsifier Framework v1.0.10

**Framework:** external `SST_Falsifier_Framework_v1.0.10`, exact `CANONICAL_FROZEN` RC2 ZIP; never modified or bundled.
**Atlas adapter:** external `A003_Fourier_Knot_Import_Adapter_v0.2.3`, exact pinned-source SHA256, no vendoring.
**Required original atlas:** adjacent `A003-v0.1.2` containing `manifest.json` + all 384 `xyz/*.xyz` entries. The adapter ZIP does **not** include the atlas.
**Source class:** A003 Fourier trefoils are `GEOMETRIC_SEEDS_ONLY`. The derived 3D Gaussian vorticity, velocity and pressure are **synthetic** even after successful import. Physical Euler / PKLSA, Casimir and gravity remain UNRESOLVED.

## Windows folders

- `C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A003_Fourier_Knot_Seed_Atlas\A003_Fourier_Knot_Import_Adapter_v0.2.3`
- `C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A003_Fourier_Knot_Seed_Atlas\A003-v0.1.2`
- `C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.10`

Recommended commands:

```bat
run_all.cmd VERIFY
run_all.cmd SELFTEST
run_all.cmd A003
run_all.cmd CORE3D
run_all.cmd ALL
```

If automatic discovery fails, set `SST_A003_ADAPTER_ROOT`, `SST_ATLAS_ROOT` and `SST_FALSIFIER_FRAMEWORK_ROOT` to those directories. Do not silently switch source families. `A003` writes `outputs/A003_V039_RESULT.json` within the unique run workspace and will accurately report an absent atlas as `NOT_RUN_PREREQUISITE`. `ALL` always attempts both the independent software and scientific diagnostics under the framework 1.0.10 `FAIL != STOP` policy; physical claims are never promoted.

Gate definitions: G33 immutable adapter release; G34 original 384-input atlas validation; G35 independently source-verified 3D **synthetic** Gaussian surrogates and core/holdout diagnostics; G36 native physical PKLSA Euler field remains unresolved without separate provenance. G2/G11/G13/G24/G29/G31 historical failures are retained.
