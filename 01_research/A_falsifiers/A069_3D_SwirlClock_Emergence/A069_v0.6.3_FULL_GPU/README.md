# A069 v0.6.3 FULL GPU — Intel Arc A770, checkpoint continuation + source-native high grids

**Status: `DEVELOPMENT_NOT_FROZEN_NOT_CERTIFIED`.** This release contains a **complete PyTorch XPU 3D GP evolution runner**, not just the old bulk preflight. It is **NOT** the signed/sandboxed official v1.0.10 framework instance, and no physical trefoil stability or Swirl Clock has been demonstrated. It neither overwrites earlier A069 code nor changes earlier BLIND runs.

## Scientific model and source integrity

Solve `i dψ/dT = -(1/2) ∇²ψ + μ(|ψ|² − 1)ψ`, Strang split-step, `μ=1/(2ξ²)`. The `ξ↔μ` relation uses a **planar soliton width convention only**; it is not evidence that a 3D knotted vortex is stationary or solves incompressible Euler. XPU uses `complex64` throughout propagation; CPU-FP64 verifies the first requested continuation steps, independently using NumPy. Its relative error threshold is **numerical screening**, not physics certification. Surface-mapped 2015 A/B parametrizations come from the byte-pinned v0.5.0 source archive SHA-256 `bb8e1d392e3e72c0c2caee22df406469f9f3de5504296da45cedc6fda8d04b6e`.

* Fourier **A** means the 2015 p.32 Fourier trefoil, not a torus knot parameterization. At **A160**: `ξ=.08`, `μ=78.125`, **G32 FAIL**. It is permitted *diagnostic only* with an explicit flag. **A512** is the first nominally geometrically admissible research grid, pending memory and empirical qualification.
* Torus **B** means the 2015 p.66 parametric torus trefoil. **B160**, **B192**, **B256**: `ξ=.28`, `μ≈6.37755102040816`, geometry screen passes. Physical G34/G35 remain UNRESOLVED.
* Never upsample an evolved B160 checkpoint into B256 and call it independent grid convergence: B192/B256 seed **from the same original source geometry**, with the identical GP coupling and preparation prescription.

## Hardware and installation

Only the **Intel Arc A770 (16 GB)** is allowed for `--backend xpu` (strict name `A770`, no fallback to CPU/iGPU). Reuse the already-working `.venv-xpu` from `gp_xpu_probe.py`, or create it in this directory. Install Intel XPU PyTorch **in a separate environment**, not the normal Workbench Python environment. Windows example:

```bat
py -3.14 -m venv .venv-xpu
.venv-xpu\Scripts\python.exe -m pip install -r requirements.txt
.venv-xpu\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/xpu
.venv-xpu\Scripts\python.exe bootstrap_upstream.py
.venv-xpu\Scripts\python.exe -m pytest -q tests
```

Set `A069_XPU_PYTHON` to the absolute tested `python.exe` path if your `.venv-xpu` lives elsewhere; `run_known_checkpoints.cmd` uses this override.

## Start with YOUR two existing v0.6.2 checkpoints

The batch script checks both absolute paths **before** running. These files are on **your Windows PC**, not provided in this development ZIP:

```text
C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A069_3D_SwirlClock_Emergence\A069_v0.6.2\results\checkpoints\B160\20261019T142950548208Z\T000016.npz
C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A069_3D_SwirlClock_Emergence\A069_v0.6.2\results\checkpoints\A160\20261019T143016722791Z\T000016.npz
```

```bat
run_known_checkpoints.cmd
```

Equivalent manual commands (the absolute total of 32 steps means **16 extra GP steps**, not 32 new steps):

```bat
.venv-xpu\Scripts\python.exe gp_full_xpu.py --case B160 --init checkpoint --checkpoint "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A069_3D_SwirlClock_Emergence\A069_v0.6.2\results\checkpoints\B160\20261019T142950548208Z\T000016.npz" --total-steps 32 --diagnostic-every 4 --checkpoint-every 8 --cpu-parity-steps 2
.venv-xpu\Scripts\python.exe gp_full_xpu.py --case A160 --init checkpoint --checkpoint "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A069_3D_SwirlClock_Emergence\A069_v0.6.2\results\checkpoints\A160\20261019T143016722791Z\T000016.npz" --total-steps 32 --diagnostic-every 4 --checkpoint-every 8 --cpu-parity-steps 2 --allow-unqualified-geometry
```

**All outputs are create-once under** `results/<CASE>/<UTC_RUN_ID>/`, containing `RUN_RESULT.json`, `T000024.npy` and `T000032.npy` plus cryptographic `T*.json` sidecars. The original `.npz` checkpoints are never mutated. `--init generated --checkpoint results/.../T000032.npy --total-steps 48` safely resumes a newer GPU checkpoint.

## Independently seeded high-resolution grids

```bat
.venv-xpu\Scripts\python.exe gp_full_xpu.py --case B192 --init seed --total-steps 16 --cpu-parity-steps 0
run_optional_b256.cmd
```

These runs call the *byte-pinned v0.5.0* oriented 2-chain solid-angle initializer, but process 3D space in thin z-/x-slabs to constrain host RAM. Seeding itself is **CPU/Numba**, and time integration is **GPU/XPU**; do not describe the entire initializer+solver as GPU-only. The source-native new field is stored in `complex64` with its own SHA-256. The stepper uses identical GP equations to v0.6.2 and a different numeric precision. Seeds created from source are **not independently sourced physical experiments**.

**A512:** only after B256 measurements and available VRAM review:

```bat
run_optional_a512.cmd
```

The GPU VRAM safety guard is deliberately conservative and cannot be overridden in this release. A512 may be rejected on 16 GB: reducing requested resources, devising a genuine memory-optimized FFT or streaming solver, or using larger-memory hardware is then necessary; never claim 512³ was successfully run without a real measured result. A512 source-native CPU solid-angle seeding is also computationally expensive.

## Separate offline subgrid topology

After `gp_full_xpu.py` has emitted snapshots:

```bat
.venv-xpu\Scripts\python.exe analyze_snapshot.py --field "results\B160\RUN_ID\T000024.npy" --out "results\B160\RUN_ID\topology_T24.json"
.venv-xpu\Scripts\python.exe analyze_snapshot.py --field "results\B160\RUN_ID\T000032.npy" --offsets --out "results\B160\RUN_ID\topology_T32.json"
```

The snapshot reader **upcasts GPU complex64 fields to complex128 for strict phase winding**, retaining the original integer-winding tolerance rather than silently relaxing it. It computes subgrid face zeros, closed dual graph components and five rotated Fox determinants. `--offsets` additionally tests spectral shifted sampling. Analysis runs on CPU in a separate process so device memory is not retained. For >256³, the analyzer explicitly refuses by default because a robust whole-domain 512³ topology analysis is not yet memory qualified.

**A Fox determinant of 3 on two snapshots is NOT proof of continuous ambient isotopy, no reconnection, four clock cycles or independent physical replication.** For G34 one must sample all intervening times, test topology with sufficient spatial/temporal convergence and track event neighborhoods; currently G34 and G35 are `UNRESOLVED`.

## Framework v1.0.10 adapter

v1.0.10 currently identifies as `LOCAL_VALIDATED_CANDIDATE` in the inspected Google Drive release. The source’s C++/SYCL/DD32 kernels are not the same thing as a validated 3D-GP FFT backend. This package provides **two separate mechanisms**:

1. `framework_v110_export.py`: creates a conservative JSON gate-evidence file and marks all physical reveal eligibility blocked; this is available without installing the framework.
2. `run_framework_adapter_v110.py`: **imports and actually calls** the externally installed `sst_falsifier.gates.GateLedger.run_evaluators` v1.0.10 and derives qualification separately from PASS/FAIL. Requires explicit `--framework-root` and checks version/path, refusing ambient substitutes. This is still NOT a full officially signed framework-instance run:

```bat
.venv-xpu\Scripts\python.exe run_framework_adapter_v110.py --framework-root "C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.10" --result "results\B160\RUN_ID\RUN_RESULT.json" --out "results\B160\RUN_ID\FRAMEWORK_V110_LEDGER_ADAPTER.json"
```

No existing A069 source version, signatures, or BLIND results are rewritten. An official new instance must be separately created and qualified by the actual framework runner before FREEZE/REVEAL.

## Measurement interpretation and limits

`metrics()` evaluates GP Hamiltonian kinetic energy by **spectral Parseval** on the device, avoiding three inverse FFT gradients. PyTorch FP32 reductions can differ from NumPy FP64 at small relative tolerances; use a separate FP64 diagnostic whenever energy conservation controls science qualification. GPU VRAM peak is reported as allocator bytes but may **exclude native FFT library workspace**. Report wall time excludes slab seeding and initial device allocation; the `RUN_RESULT.json` records the evolution and checkpointer wall time. CPU-FP64 parity on 160³ is tested for the first two steps and does not certify the entire trajectory.

`G32` = source-native geometry screen (raw PASS/FAIL, diagnostic authority only); `G33` = snapshot topology diagnostic (not an unbroken time proof); `G34` = continuous topological stability UNRESOLVED; `G35` = real intrinsic phase-clock UNRESOLVED. No Pauli/Lorentz/Compton/SST clock law is passed into the GP solver. No third-party KnotPlot relaxation is admitted as dynamics-ready physics.

### Optional empirical VRAM-guard calibration before A512

The default estimate (`112 bytes/voxel` plus reserve) may reject A512 even when an optimized run *might* fit. Once a **real** XPU `B256` run exists, use `--vram-calibration-run "results\B256\RUN_ID\RUN_RESULT.json"` with your A512 command. This reads the **measured** PyTorch peak-reserved-byte count, adds 25% screening headroom (at least 90 bytes/voxel), and still enforces the 88%-of-free-VRAM bound. An N160/CPU/synthetic file cannot serve as calibration. This is NOT a measured A512 peak or proof of memory safety; PyTorch's counter may miss native FFT workspaces. The code retains the underlying hard memory guard, checks device allocation and never claims an A512 success unless the calculation actually finishes.

## Time-step convergence on GPU (new source-native simulations)

For a valid time-step ladder, keep the same original geometry, box, xi and GP coupling and compare at the **same final physical dimensionless time**. For B256:

```bat
.venv-xpu\Scripts\python.exe gp_full_xpu.py --case B256 --init seed --dt 0.003 --total-steps 16 --cpu-parity-steps 0
.venv-xpu\Scripts\python.exe gp_full_xpu.py --case B256 --init seed --dt 0.0015 --total-steps 32 --cpu-parity-steps 0
```

Both terminate at T=0.048. This is a separate new campaign, not a continuation of the old B160 checkpoint. Time-step override is **forbidden** for checkpoints to preserve their pinned science identity. Compare norm, Hamiltonian, filament centerline distance and topology at matched physical times before drawing any convergence conclusion.