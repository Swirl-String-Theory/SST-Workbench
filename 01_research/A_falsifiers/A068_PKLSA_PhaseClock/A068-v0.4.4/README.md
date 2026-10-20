# A068 — v0.4.5 engineering diagnostic patch (DEVELOPMENT ONLY)

**Purpose:** investigate *causes* of the v0.4.4 T=20 material-tube failure without modifying frozen scientific source, gate ledger, A004, framework v1.0.10, or prior BLIND output. This ZIP is **not** an official A068 v0.4.5 release, and does **not** certify a material vortex tube, RPO, Floquet mode, GPU or SST physics. An actual v0.4.5 instance requires a new framework-generated instance, new source manifest, science contract, gates, freeze and blind run.

## Key audit of v0.4.4

1. `experiment/material.py::sample_vector` transports particles with trilinear interpolation. This does not preserve Euler's spectrally enforced solenoidality between nodes. Its divergence can differ greatly from the spectral-field divergence.
2. `experiment/long_material.py` evaluates `det F` solely through six satellite tracers, not by the independent variational equation.
3. `experiment/long_material.py::surface_quality_screen` samples only some triangle bounding spheres. A negative result cannot exclude self-intersections. The signed volume of a self-intersecting polygonal mesh is an algebraic signed volume rather than necessarily a physical enclosed volume.
4. The v0.4.4 fixed geometric torus starts with excessive vorticity-normal flux. Streamlines of omega must first define a numerical invariant flux surface; not every 3D Euler vorticity field possesses a smooth embedded invariant torus.
5. Intel Arc A770 (Arc A-Series) does **not** have native FP64. The correct reference is CPU FP64, compared with real XPU FP32 and optionally framework SYCL DD32 **common-kernel screening**. DD32 does not certify complete Euler solver equivalence.

## Included diagnostic modules

- `diagnostics/variational.py`: simultaneous Euler RK4 / material point / deformation gradient, both exact Jacobian of A068 trilinear interpolant and Fourier reconstructed solenoidal velocity. Can compare F'=(grad u)F with finite-difference satellites.
- `diagnostics/fieldline_tube.py`: first same-direction Poincare-section return of a cross-sectional ring, with set-wise matching (can rotate) and no fake closure by joining mismatched endpoints. Produces only a candidate.
- `diagnostics/mesh_intersections.py`: no subsampling; all topologically disjoint triangle pairs screened by cKDTree enclosing spheres, AABB, floating-point SAT, with limitations explicitly reported. All face neighborhoods are enumerated; incident triangles and exact-predicate boundary cases are NOT certified. Don't promote this to exact global embeddedness.
- `native/exact_mesh_check.cpp`: optional, not yet locally compiled CGAL `Polygon_mesh_processing::self_intersections` using exact predicates for binary64 snapshot coordinates. Needs CGAL on Windows and independent compile/test. Reports snapshot-only result, not continuous-time embeddedness.
- `diagnostics/export_mesh.py`: exporter for `EULER_3D_FIELDS_MODEL_ONLY.npz` unwrapped material mesh to CGAL tool text input. Run: `python -m diagnostics.export_mesh EULER_3D_FIELDS_MODEL_ONLY.npz --index -1 --output mesh.txt`.
- `diagnostics/xpu_probe.py`: read-only exact device/FFT smoke and capabilities, explicit no native FP64 claim. `SETUP_XPU_SEPARATE_ENV.cmd` (OPT-IN) installs official PyTorch XPU wheels in a separate Python 3.12 virtual environment. Existing A068 / framework venv untouched. `PROBE_XPU.cmd` repeats checks.
- `TREFOIL_SHORT_MODEL_AUDIT.json`: actual original KnotPlot-seeded field short test (N=16,a=0.4,T=0.2); this is **nonblind development evidence**.
- `V044_INTERSECTION_AUDIT.json`: actual saved v0.4.4 CERTIFY 32x10 material mesh snapshots; counts are numerical, not CGAL-certified.

## How to use in a future A068 v0.4.5 instance

1. Keep v0.4.4 frozen. Instantiate new `A068-v0.4.5` with pinned framework v1.0.10 after verifying its qualification; copy these development modules under `experiment/` only after auditing and adding their exact SHA-256 values to a **new** source contract.
2. G1: validate A004 v0.2.2 hashes and the new module hashes; G2: compare Fourier/trilinear divergence, RK4 parity, exact spectral-gradient calculations and epsilon/dt refinement.
3. G3a (initial): trace actual vorticity field lines and Poincare return map, obtain closed, embedded toroidal flux-surface candidate or fail-closed `UNRESOLVED`. Do not call every material torus a vortex tube.
4. G3b (dynamic): transport exact same surface using Fourier velocity, solve `F'=(grad u)F` and paired satellites; check |det F-1| against time step, grid n and interpolation errors; compare polygon signed volume ONLY while mesh is embedded.
5. Mesh: at each sampled time run full nonincident SAT test, followed by independent CGAL exact-predicate face-pair verification for all topological adjacency cases. To certify **throughout** [0,T], one must additionally bound motion between samples (continuous collision detection or certified interval bounds); selected snapshots alone never prove it.
6. Run RPO shooting and time-dependent Floquet/Arnoldi **after** a qualified material vortex and numerical convergence; all independent numerical diagnostics may still execute under v1.0.10, but physics gates stay unresolved or diagnostic-only.
7. GPU: independently create XPU venv; test PyTorch XPU FP32 FFT then full RK4 solver parity vs CPU NumPy FP64 with fixed seeds, step count, grid, CFL, energy/helicity, conservation, and 3D-field residual; optional common-kernel SYCL DD32 is `SCREENING_ONLY`. Never label Arc A770 native FP64. No implicit fallback.

## Test

```bat
py -m pytest -q tests
```

5 standalone Python regression tests pass on Linux/NumPy/SciPy (CPU) in the authoring environment. The optional CGAL tool has **not** been compiled here; the Intel Arc XPU test has **not** been run on the target hardware.

### CGAL optional build

```
cmake -S native -B native/build -DCMAKE_BUILD_TYPE=Release
cmake --build native/build --config Release
python -m diagnostics.export_mesh EULER_3D_FIELDS_MODEL_ONLY.npz --index -1 --output mesh.txt
native/build/Release/exact_mesh_check.exe mesh.txt
```

## Sources and risk boundaries

- A068-v0.4.4 one-click source overlay; `experiment/euler3d.py`, `material.py`, `mesh_refinement.py`, `long_material.py`, `vortex_seed.py`, `gpu_xpu.py` examined without mutation.
- A068-v0.4.4 CERTIFY output fields from `PKLSA_PhaseClock_v0.4.4-outputs.zip` inspected.
- Exact vorticity topology, finite-core material vortex, physical time calibration, original SST hypotheses and native Arc FP64 are **not** established.
