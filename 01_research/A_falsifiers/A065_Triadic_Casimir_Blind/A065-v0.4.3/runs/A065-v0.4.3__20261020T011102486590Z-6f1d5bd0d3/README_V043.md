# A065-v0.4.3 — Independent Post-export FFT and Longer Arc A770 Euler

**Release class:** numerical diagnostics / DEVELOPMENT, not physical PKLSA certification.  
**Upstream:** byte-unchanged frozen framework v1.0.10, A003 adapter v0.2.3, source and seals inherited from v0.4.2.

## Scope

- **G49:** source/operator SHA-256, installed dpnp/dpctl compiled binary hashes, Intel Arc A770 Level Zero identity, driver and package versions. This is a **partial execution fingerprint**, NOT a certified full oneMKL/driver JIT build. Full binary closure stays unverified.
- **G50:** independent FFT residual audit of all six *serialized* CPU FP64 fields: div(u), curl(u)-omega, pressure Poisson and energy drift.
- **G51:** same four independent checks on all six *serialized* GPU FP32 fields, with separately frozen FP32 tolerances and no precision promotion.
- **G52:** verify all 12 initial and final field datasets; 3 full voxel snapshots per trajectory at t=0, .04, .08, and 5 diagnostic records at t=0,.02,.04,.06,.08.
- **G53:** independently compare the *serialized* 16-step and 32-step final u, omega, p fields at T=.08; no parameter refit.
- **G54:** never promote synthetic Gaussian A003 initial conditions to physical PKLSA validation.

Fixed geometries: `torus_3_1_direct`, `torus_3_1_hoste`; N=48,64,96; A003 1200 points, stride=6. Fixed L=12, Gamma=1, assumed Gaussian a=.55 and density=1. The original v0.4.0 T=.02 and 4 steps are **not changed**; the new longer diagnostic track uses independent `POST_EXPORT_V043.json` with T=.08, steps=16/32.

## Running on Windows

In `A065-v0.4.3`, use the **working** virtual environment that already has dpnp 0.20.0, dpctl 0.22.1 and the oneAPI Arc Level Zero stack. The original framework v1.0.10 and A003 directories are separate, unmodified installations.

```bat
set "SST_FALSIFIER_FRAMEWORK_ROOT=C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.10"
set "SST_A003_ADAPTER_ROOT=C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A003_Fourier_Knot_Seed_Atlas\A003_Fourier_Knot_Import_Adapter_v0.2.3"
set "SST_ATLAS_ROOT=C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A003_Fourier_Knot_Seed_Atlas\A003-v0.1.2"

run_all.cmd VERIFY
run_all.cmd SELFTEST
run_all.cmd GPU_EXTENDED
```

`GPU_EXTENDED` computes CPU/Arc 48/64/96 volumes, saves initial/final, three field snapshots and fine-endpoint arrays, generates independent post-export metrics and `POST_EXPORT_V043_REPORT.pdf`. The Arc requirement is strict: no GPU -> nonzero exit status and a useful PDF/`NOT_RUN_PREREQUISITE`, **not** a CPU substitution. Expect larger runtime and BLIND_RESULTS.zip sizes than v0.4.2.

For a separate independent re-audit of the newly exported blind ZIPs, pass paths to `POST_EXPORT` (use absolute Windows paths, e.g. two `_BLIND_RESULTS.zip` archives):

```bat
run_all.cmd POST_EXPORT "C:\path\CPU_BLIND_RESULTS.zip" "C:\path\GPU_BLIND_RESULTS.zip"
```

Or rerun the audit on the files created by `GPU_EXTENDED` by passing its exported `..._BLIND_RESULTS.zip`, which includes all twelve saved volumes:

```bat
run_all.cmd POST_EXPORT "C:\path\A065-v0.4.3__RUNID_BLIND_RESULTS.zip"
```

The post-export audit independently *re-reads actual .npz bytes*, rejects wrong file precision, shape or inconsistent trace endpoints and never silently accepts missing pressure/energy evidence. An old v0.4.2 export can give G50=PASS, but GPU G51 remains UNRESOLVED without initial GPU fields; G52/G53 are NOT_RUN_PREREQUISITE.

The official v1.0.10 FRAMEWORK can register G49-G54; within an independent new framework instance, gates without imported or locally executed v0.4.3 extended evidence **must** remain NOT_RUN_PREREQUISITE. Historical G0-G48 and their failures stay unchanged.

## Equations and gauges

For exported `u`, `omega`, `p` with rho=1, the numerical checks recompute independently

\[
\nabla\cdot\mathbf u,\qquad \nabla\times\mathbf u-\boldsymbol\omega,\qquad
q=\frac p\rho+\frac12|\mathbf u|^2,\qquad
\nabla^2q-\nabla\cdot(\mathbf u\times(\nabla\times\mathbf u)),
\qquad E=\frac\rho2\int_{[0,L]^3}|\mathbf u|^2\,dV.
\]

All Fourier derivatives are re-evaluated in CPU FP64 *from saved rounded voxels*, not copied from on-run residual summaries. This tests **internal numerical consistency**, not independently measured pressure. Time refinement is an IVP check, not long-time Euler convergence or physical PKLSA evidence.

## Verification and release rules

- All earlier scientific data/seals/preregistrations remain byte-identical; v0.4.3 adds only `POST_EXPORT_V043.json`, SHA pin and new source/evidence logic.
- New RUN_IDs and archives use exclusive creation; older local exports are never overwritten.
- No GPU available in non-Arc development environment: new numerical GPU gates remain unexecuted.
- The full official `FULL` phase and actual Arc extended execution must be checked on the Windows target before any release is promoted beyond DEVELOPMENT.

## Official framework evidence import (optional, explicit)

Framework `FRAMEWORK` uses a new isolated instance. It does **not** implicitly import a previous `GPU_EXTENDED` run. To register independently recomputed post-export gate results in the official v1.0.10 `FULL` ledger, point explicitly at the exported v0.4.3 BLIND_RESULTS.zip (or a deliberately chosen earlier archive):

```bat
set "SST_A065_V043_EVIDENCE_ZIP=C:\path\to\A065-v0.4.3__RUNID_BLIND_RESULTS.zip"
run_all.cmd FRAMEWORK
```

The new instance reopens the ZIP and independently recalculates G50/G51/G52/G53. The archive SHA256 is recorded; malformed or contradictory files fail closed. G49 does not become PASS from an archive alone: the source/binary operator fingerprint is a separate local device-execution claim requiring validated provenance. The physical G54 remains UNRESOLVED. Without the explicitly supplied ZIP, framework G49–G53 remain NOT_RUN_PREREQUISITE.
