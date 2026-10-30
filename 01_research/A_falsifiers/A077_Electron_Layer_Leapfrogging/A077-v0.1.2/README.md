# A077-v0.1.2 | Electron Layer & Leapfrogging Unknots

**Status: DEVELOPMENT / DIAGNOSTIC ONLY.** This v0.1.2 is restricted to the G10 lifecycle correction. It does not establish electron spin 1/2, quantized layers, a material knotted/unknotted Euler solution, or physical particle existence.

## Source integrity and version migration

- New create-only A077-v0.1.2. Do not unzip on top of A077-v0.1.0.
- Constructed using official SST Falsifier Framework v1.1.0 canonical source generator with 142 hash-verified embedded source files. No missing `outputs.py` or `test_outputs.py`.
- The original v0.1.0 output archives remain historical, independently inspectable evidence. Do not edit their frozen protocol.
- Project family location: `01_research/A_falsifiers/A077_Electron_Layer_Leapfrogging/A077-v0.1.2/`.
- The SOURCE_PRIVATE ZIP contains *new* reveal/opaque ID secrets; do not publicly distribute it. The Framework BLIND output ZIP excludes those secrets.

## Windows: correct order from A077-v0.1.2

```cmd
python -m pip install numpy scipy matplotlib pytest pybind11 setuptools reportlab
python -m pytest -q tests
call tools\build_cpp.cmd
run_all.cmd BACKEND_PREFLIGHT
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd FULL
run_all.cmd CERTIFY
```

`run_all.cmd ATLAS_VERIFY` is not needed (the E010 atlas is not used for these analytic inputs). If the underlying framework is running GPU profile, do not pretend a probe counts as scientific execution; this package uses the CPU profile and runs Python+native C++.

Run the separate exploratory full-field test (not automatic scientific gate promotion):

```cmd
run_euler_pilot.cmd
```

Optional advanced grid/time pilot: edit `configs/euler_pilot.json` **before running**. To make it a preregistered gate for publication instead of a research-only exploratory test, create a *new version*; do not change the already frozen v0.1.2 protocol.

## Output scheme

- Framework canonical output `electron_layer_leapfrogging_v0.1.2-outputs/`, with immutable run IDs and `science_diagnostics/`.
- Raw CSV for **all timesteps** of the `single`, `same`, `opposite`, `reverse` scenarios, plus event brackets, surface clearance and refined endpoints.
- Framework BLIND ZIP, SHA-256 sidecar and full 16-section frozen LaTeX PDF published adjacent to the version directory.
- Separate `A077_euler_pilot_v0.1.2-outputs/` from `run_euler_pilot.cmd`: raw field NPZ and machine-readable conservative diagnostics, not an Euler-certified spin test.

## Falsifiable gates

- G0/G1: protocol + input hashes.
- G2: separate quadrature and temporal RK4 refinements; event-root convergence. Core contact is a *separate physical applicability limiter*.
- **G5**: truly executed instance C++/pybind11 science parity, independent of G4.
- **G10**: framework's independent two-of-three backend category count and numeric parity only.
- G3/G4/G8: UNRESOLVED physical claim gates. G6/G7 disabled by CPU-only/no-independent-data profile, G9 DEFERRED.
- P01--P07 are descriptive subtests of the prior plan, not evidence to promote G8.

## Physical caveats

The reduced ring trajectories satisfy an *imposed* core volume proxy and cannot certify incompressible Euler vorticity evolution. Positive *sampled* clearance in circular geometry does not certify contact-free three-dimensional material tube evolution. The optional Euler field is a short-time 2/3-dealiased *periodic* spectral Galerkin discretization of inviscid incompressible Euler with smooth width, not exact isolated finite-core material vortex tubes. Independent meridional/azimuthal velocity control is not a quantum number. A real vector velocity field cannot by itself exhibit physical spinorial `2pi -> -1` state holonomy. No spin/electron claims can be made without a separately justified physical state bundle and continuum tests.

## G10 v0.1.2 lifecycle fix

`experiment/pipeline.py` uses `experiment/g10_lifecycle.py` to evaluate all enabled pre-backend gates while intentionally reserving G10. The original, unmodified Framework runner then executes both real science backends, writes `AUTO_BACKEND_MATRIX.json`, computes `assess_numeric_control`, and registers G10 from evidence. The pipeline is forbidden from registering G10 or manufacturing a PASS. Numeric parity does not imply physical G8 qualification.

Regression tests in `tests/test_g10_v012.py` exercise PASS, FAIL, unavailable backend, invalid tolerance, premature gate assertion, disabled gates and scientific UNRESOLVED propagation. If no real C++/GPU scientific backend exists, framework FULL returns nonzero (typically 3) with diagnostic outputs, not a scientific PASS.

Version-specific credentials are fresh; no v0.1.1 freeze or output is overwritten. See `VALIDATION.md`.
