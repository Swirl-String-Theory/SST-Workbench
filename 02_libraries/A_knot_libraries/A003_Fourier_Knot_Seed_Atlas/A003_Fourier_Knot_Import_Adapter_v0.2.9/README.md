# A003 Fourier Knot Import Adapter v0.2.9 — G6 PKLSA/C005 diagnostic handoff

**Status: DIAGNOSTIC IMPLEMENTATION. G5 bounded F3/F4 PASS carries forward; G6 Euler/PKLSA remains UNRESOLVED until time integration is executed with a qualified provider.** This is a new versioned sibling release. It never modifies A003 v0.1.2, earlier adapter versions or `site-packages`.

## Framework v1.0.10

Use **exact** `SST_Falsifier_Framework_v1.0.10` (SHA256 `sst_falsifier/gates.py`: `e5756c90a34d482e3dec7e0e9a22a131f7b8968f5de492832963f3063008a055`). `GateLedger.run_evaluators` continues after scientific FAIL while separately recording `qualification` and `execution_status`.

The user's recent A003 v0.2.8.1 live report labels their installed framework `CANONICAL_FROZEN`. The Drive copy reviewed while building this adapter still exposes `RELEASE_INFO.json` status `LOCAL_VALIDATED_CANDIDATE`. **Do not promote the remote copy from inference**. G6P0 checks the **installed** framework metadata; if not frozen, it records `UNRESOLVED` but allows diagnostic execution. Hash mismatch stops execution. This is a GateLedger integration, **not** a fully generated blind/reveal framework instance.

## Source-native modules (no duplicate numerical kernels)

- `A003-v0.1.2` = hashed geometry source, 384 XYZ, including F3/F4 (N=1200/2400/4800).
- `E010-v0.3.1/sst_pklsa` = PKLSA source/geometry/discovery/qualification facade. **It does not supply Euler time dynamics.** Its presence is checked, but A003's carrier is **not declared admitted** to E010 without an explicit lineage registration.
- `C005-v0.6.1/fermat_ext.core` = the existing source-native `backend_biot_savart_with_jacobian` finite-core Rosenhead-midpoint field and analytic spatial Jacobian. Called directly with `force_python=True`, `auto_build=False`; no copied kernel and no MSVC/SYCL/GPU parity claim.
- `a*=0.05` atlas coordinate units is an **assumed uncalibrated** finite-core scale, not the SST `r_c` derived from dynamics. C005's built-in coefficient follows its own beta model. All field results remain dimensionless/model diagnostics.

The default pilot uses the real A003 XYZ centerlines for **F3 and F4** at **N=1200, 2400, 4800**, and a fixed six-probe family per seed. Source hash checks are repeated. Relative field differences, finite-valued velocity/Jacobian, and `trace(J)/||J||` diagnostics are recorded. Neither the analytic divergence diagnostic nor spatial convergence proves Euler temporal evolution or knot stability.

## Windows commands

Unzip as sibling to `A003_Fourier_Knot_Import_Adapter_v0.2.8.1`:

```bat
cd /d C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A003_Fourier_Knot_Seed_Atlas\A003_Fourier_Knot_Import_Adapter_v0.2.9
set "SST_FRAMEWORK_ROOT=C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.10"
where python
python -c "import json,os; print(json.load(open(os.path.join(os.environ['SST_FRAMEWORK_ROOT'],'RELEASE_INFO.json')))['status'])"
run_all.cmd
run_all.cmd G6
```

If latest already-qualified v0.2.8.1 G5 summary is not autodiscovered, pass its file path:

```bat
run_g6_pklsa.cmd --g5-summary "C:\path\to\A003_Fourier_Knot_Import_Adapter_v0.2.8.1-outputs\<run_id>\QUALIFICATION_SUMMARY.json"
```

For a combined fresh G5 four-resolution provider run followed by G6 even after scientific FAIL:

```bat
run_all.cmd COMPLETE
```

`COMPLETE` stops on fatal G5 integrity failure (`exit 4`). Otherwise it continues to G6 and preserves G5 nonzero status. Source/provider execution exceptions are fatal; they are never disguised as scientific FAIL. `G6` normally returns **exit 3 (UNRESOLVED)** until a coupled native Euler trajectory solver is qualified. A numerical FAIL returns 2.

Preflight without running C005 field:

```bat
run_g6_pklsa.cmd --preflight-only
```

Optional `SST_WORKBENCH_ROOT` selects your actual Workbench root; optional `--e010-root`, `--c005-root` override exact paths. `--epsilon 0.05` is a dimensionless/core diagnostic hypothesis, not physically certified.

## Outputs

Unique, non-overwriting sibling `A003_Fourier_Knot_Import_Adapter_v0.2.9-outputs/<run_id>/`:

- `G6_READINESS_SUMMARY.json` — true G5 evidence receipt (paired ledger digest + raw provider), E010/C005 source paths/hash, framework metadata, explicit physical limits.
- `GATE_LEDGER.json` — exact v1.0.10 software gate results, qualifications and execution statuses.
- `G6_FINITE_CORE_PROBE.json` — measured C005 velocity/Jacobian, divergence and multi-resolution convergence, or clearly NOT_EXECUTED.
- `A003_G6_PKLSA_DIAGNOSTIC_REPORT.pdf` — PDF diagnostic where reportlab installed, otherwise `PDF_RENDER.json` explains missing PDF.

## Gate contract

| Gate | Required result | Interpretation |
|---|---|---|
| G6P0 | Framework source hash and locally stated frozen metadata | Framework identity, no implicit canonical promotion |
| G6P1 | 384/384 A003 sources and measured, ledger-hashed G5 receipt | Only bounded F3/F4 topology screen |
| G6P2 | E010 module installed at canonical path | Source presence, **not A003 registration** |
| G6P3 | C005 field/Jacobian executed | Instantaneous kernel test, not Euler evolution |
| G6P4 | C005 F3/F4 field converges at N=1200/2400/4800 | Spatial convergence only |
| G6P5 | Low trace(J) / norm(J) | Differential incompressibility diagnostic |
| G6P6 | Explicit A003→E010 admitted carrier identity/lineage | **UNRESOLVED/NOT_EXECUTED** in this release |
| G6P7 | Coupled Euler finite-core time evolution with dt/N ladders, conservation and topology tracking | **UNRESOLVED/NOT_EXECUTED**; no suitable verified E010/C005 time trajectory path yet |
| G6 | Valid PKLSA dynamical qualification | **UNRESOLVED** until G6P6/P7 pass; independent software PASS is not physical proof |

**Next scientific tranche:** implement native A003→E010 carrier registration with immutable hashes, then connect a *source-identified* existing Euler/RK4 filament solver (not the photon/geodesic ray `integrate_ray` in C005). Test dt halving, N refinement, circulation/energy diagnostics, topology under trajectory, and non-short-circuit gates. Keep gravity, self-confinement, Swirl Clock and other physical SST claims explicitly outside this pilot.
