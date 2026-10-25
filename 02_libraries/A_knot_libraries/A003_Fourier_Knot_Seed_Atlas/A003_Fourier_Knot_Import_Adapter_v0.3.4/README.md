# A003 Fourier Knot Import Adapter v0.3.4

**Scientific state:** DEVELOPMENT; 3D Euler benchmark implemented, but full G6 physical qualification **UNRESOLVED**.
**Parent:** A003 v0.3.3; all original outputroots and source files remain immutable.
**Framework:** SST Falsifier Framework v1.0.10; E010 v0.3.2 parent, optional E010 v0.3.3 installed registry; C005 v0.6.1; A058 native KnotPlot KPF decoder.

## Install locally (Windows)

Extract **A003 v0.3.4** next to existing A003 versions, and **E010 Canonical Carrier Registry v0.3.3** in a temporary tools directory. Do NOT rename E010 v0.3.2 to v0.3.3.

1. Run `python -m unittest discover -s tests -q` inside A003 v0.3.4.
2. In the extracted E010 registry release directory, run:

```bat
python e010_registry_v033.py --base "C:\workspace\projects\SST-Workbench\01_research\E_pipelines\E010_pklsa_parametric_knot_link_seed_atlas\E010-v0.3.2" --target "C:\workspace\projects\SST-Workbench\01_research\E_pipelines\E010_pklsa_parametric_knot_link_seed_atlas\E010-v0.3.3" --workbench "C:\workspace\projects\SST-Workbench" --atlas "C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A003_Fourier_Knot_Seed_Atlas\A003-v0.1.2"
```

Install is **create-only** and stops on any wrong parent config/core/hash or altered raw carrier. The old E010 v0.3.2 tree is not modified. It does not magically make the derived analytic carriers empirical evidence. To independently recheck, add `--verify` and repeat same flags. A deployed E010 v0.3.3 counts as a **local versioned registry**, not a formal framework freeze.

3. Run A003:

```bat
run_all.cmd UPSTREAM
run_all.cmd EULER
run_all.cmd COMPLETE
```

`UPSTREAM` verifies the installed E010 v0.3.3 registry. On a locally installed E010 with unchanged source SHA and native Workbench readback, **G6P8 can become PASS** in both upstream and dynamic ledgers. No local E010 copy was installed on your actual Windows machine by this release package.

For an explicit Euler projected-source diagnostic use `run_euler_v034.cmd --xyz "C:\path\to\fibonacci_torus_F3_uniform_t_N1200.xyz" --c005 "C:\workspace\projects\SST-Workbench\01_research\C_dynamics\C005_fermat_biot_savart\C005-v0.6.1"`. The resulting periodic velocity is a **projected free-space field** with deliberately different boundary conditions; never interpret it as a physical closure.

For P16 pin actual A058 `VERSION_CONTRACT.json` (Windows v0.3.7 observed) and raw 2025 KnotPlot distribution. 3.1 (47 vertices) is the F3 catalog comparison, 10.124 (102 vertices) is the F4 catalog comparison, while 8.19 (86 vertices) is **an independent 8_19 control**, not F4. Re-exporting/interpolating these to N=1200 cannot count as independent higher-resolution source.

An external E011 v0.3.0 ZIP with SHA256 `97cd1acbf23c102e4564f2d74fd329a2d03f32a29b8bd376ffa8b806c14246cc` can be supplied to UPSTREAM with `run_g6_upstream.cmd --e011 "...zip" --e011-receipt "...json"`. The receipt must match the real Gilbert raw source SHA and E011 parent ZIP SHA, with native E010 source admission. **Neither an E011 geometric receipt nor a second integrator using the same C005 RHS demonstrates independent native dynamics.** G6P16 remains unresolved without genuine independent native KnotPlot trajectory data and cross-model preregistration.

## G6P9: what was actually built

`euler_3d_qualification_v034.py` solves the incompressible inviscid Euler equation in a **three-periodic** box, with Fourier pseudospectral derivatives, Leray projection, 2/3 dealiasing, recovered pressure Poisson equation, and RK4 time stepping. It tests stationary analytic ABC (Arnold-Beltrami-Childress) flow and nonstationary Taylor-Green flow on 8/12/16 grids. Benchmarks measure pressure, momentum-algebra residual, divergence, energy drift, temporal and spatial refinement.

The optional C005 source coupling uses the genuine original C005 Biot-Savart kernel to sample velocity in a cubic grid, then changes boundary conditions by Helmholtz projection. It is **NOT** an Euler solution with physically calibrated vortex core, not equivalent to free-space filament transport; no particle/topology claim. The Euler *numerical benchmark* can PASS, while **G6P9 stays UNRESOLVED**. Periodic boundary conditions vs C005 free space, vorticity tube physical calibration, 3D source/field convergence, independent PDE code parity, and mismatch/error budgets still require independent research.

## Gate contract

- `G6P16`: UNRESOLVED until two distinct independently qualified *dynamics* providers have matching topology and comparable preregistered observables.
- `G6P8`: PASS only on local E010 v0.3.3 installed registry with native resolver, manifest and all eight analytic source SHA256 verified. Otherwise UNRESOLVED/fail-closed.
- `G6P9`: UNRESOLVED. Even a PASS ABC/Taylor-Green Euler benchmark does not demonstrate a physical A003 knot-Euler closure.
- `G6`: UNRESOLVED while source-native Euler equivalence, core calibration and independent dynamic carriers remain absent.

Existing G5 and core G6 numerical thresholds are unchanged, and all old run outputs remain untouched.
