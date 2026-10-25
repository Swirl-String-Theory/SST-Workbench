# A006 VCCR v0.2.0 — Independent Euler Qualification

**Status:** `EXACT_AFFINE_EULER_BENCHMARK_PASS / KNOTTED_NATIVE_EULER_NOT_RUN / SST_PHYSICS_UNRESOLVED`.

This is a reproducible **sidecar** built on the exact provided `A006_Volume_Circulation_CoreRadius_Closure_v0.1.0` source. The original v0.1.0 functions and the original seven tests are retained. No A006 parent sources, KnotPlot macros, ForceGrid, or `run_all.cmd` are overwritten.

## Quick start (Windows)

Install NumPy (Python >=3.10):

```bat
py -3 -m pip install -r requirements.txt
run_vccr.cmd TEST
run_vccr.cmd EULER --out Output\VCCR_v0.2.0\euler --case both
run_vccr.cmd NATIVE --input examples\synthetic_native_contract_demo.json --out Output\VCCR_v0.2.0\native
run_vccr.cmd DEMO
```

Run on macOS/Linux from the package root:

```bash
python -m pip install -r requirements.txt
python -m vccr.dispatch TEST
python -m vccr.dispatch EULER --out Output/VCCR_v0.2.0/euler --case both
python -m vccr.dispatch NATIVE --input examples/synthetic_native_contract_demo.json
python -m vccr.dispatch DEMO
```

Existing v0.1.0 `analytic`, `geometry`, `trajectory`, `compare`, `saturated`, and `bounds` subcommands remain callable (see `docs/README_v0.1.0.md`). They are conditional algebraic reconstructions and **not independent Euler qualifications**.

## New scientific evidence

`EULER` uses the exact linear, incompressible, inviscid, unforced Euler velocity field:

```
u_x = -k*x/2 - Omega(t)*y
u_y =  Omega(t)*x - k*y/2
u_z =  k*z
Omega(t) = Omega0*exp(k*t)
```

An independent 4th-order Runge-Kutta (RK4) particle integrator advects **material rings and axial tracers**. The code reconstructs each measured cross-sectional polygon area, circulation from a velocity line integral, vorticity from sampled finite-difference velocity, axial length, and swept cell volume. **Only then** does it compare to the VCCR-predicted radius.

The benchmark also evaluates finite-difference Euler momentum and divergence residuals at independent probe points, runs temporal refinement, tests circular and elliptical cross sections, and rejects a deliberately broken rotation law (`Omega(t)=constant` with `k>0`). The results are **dimensionless**, not calibrated Euler simulations at the canonical SST length/time scales.

**Important scope limitation:** the test is a local open tube in an **unbounded affine field** with uniform axial vorticity. This is a globally nonlocalized infinite-energy model, not a self-induced **finite-core vortex**, not a periodic-box Euler solve, not a closed knot, not Biot-Savart, and not a claim of stable knotted particles. It is a verification harness for material conservation under a true Euler solution.

## NEW NATIVE data intake — external solver

The `NATIVE` command reads a JSON export of *truly material-tagged* particles and their velocities. Required structure:

```json
{
  "schema": "vccr.native.material.v1",
  "source_provenance": "external_solver",
  "frames": [
    {
      "t_s": 0.0,
      "segments": [
        {
          "material_segment_id": "tubeA_segment0",
          "material_marker_ids": ["m0", "m1", "... >= 12 unique labels ..."],
          "axial_marker_ids": ["axial_low", "axial_high"],
          "axial_points_m": [[0,0,-1],[0,0,1]],
          "ring_positions_m": [[1,0,0], ["... same number of XYZ tuples as labels ..."]],
          "ring_velocities_m_s": [[0,1,0],["... XYZ velocity at each material ring vertex ..."]],
          "vorticity_flux_m2_s": 6.283185307179586
        }
      ]
    },
    {"t_s": 0.001, "segments": ["... same material IDs/marker IDs ..."]}
  ]
}
```

This illustrative schema fragment is **not valid literal runnable data**; use `examples/synthetic_native_contract_demo.json` for a complete valid sample. All values must be SI units. Axial and ring sample positions must come from tracked **fluid material labels**, not arbitrary XYZ bead indices after remeshing.

Native loader measures: polygon area and area-equivalent radius; line-integrated velocity circulation; axial arclength; segment volume proxy; alignment/planarity; and any externally supplied vorticity flux (marked **reported, not verified**). Its output can be `PASS_MEASUREMENTS_ONLY_NOT_EULER_CERTIFICATION` but will **never certify full native Euler dynamics**, because a few snapshots cannot establish pressure/momentum residuals, mesh/time convergence, topological invariance, or finite-core field consistency.

`examples/synthetic_native_contract_demo.json` is explicitly a **synthetic affine test fixture**, not a native finite-core computation. It exercises the ingestion schema only.

## Installation alongside A006-v0.5.x

```bat
py -3 install_sidecar.py --base "C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0" --check
py -3 install_sidecar.py --base "C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0" --apply
```

This installs only `tools/VCCR_v0.2.0/` and the distinct wrapper `run_vccr_v020.cmd`, preserving an existing v0.1.0 `run_vccr.cmd` without collision. Installer is create-only and refuses changed-file overwrites. Use `run_vccr_v020.cmd TEST` / `EULER` from parent A006. Existing `run_all.cmd` and physics modules stay untouched.

## Gates and falsifiable next phase

See `SCIENCE_CONTRACT.md`, `FORMULAE_EULER.md`, and `docs/V020_RESULTS.md`. The next genuinely new physical test is a material tube that evolves in an independently converged **finite-core Euler solver with true pressure and velocity field**, followed by topological and core-clearance checks on a genuine knotted input. Not fulfilled by this release.

## Provenance / source retention

The original v0.1.0 source was provided as a ZIP and has been carried forward; its seven source example XYZ files, hashes in `test_manifest.json`, code, regression tests, and original documentation in `docs/*_v0.1.0.md` are preserved. The Python code under `vccr/euler_qualification.py`, `native_qualification.py`, `dispatch.py` and the eleven new tests is the v0.2.0 addition.
