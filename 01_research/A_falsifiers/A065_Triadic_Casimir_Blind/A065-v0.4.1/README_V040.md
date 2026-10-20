# A065-v0.4.0 — A003 volume convergence + independent numerical Euler IVP

## Scientific status

- **CANONICAL FRAMEWORK**: external, unchanged SST Falsifier Framework v1.0.10 CANONICAL_FROZEN.
- **A003**: original unmodified Fourier Knot Import Adapter v0.2.3 and atlas v0.1.2;
  all 384 atlas records checked by the original adapter before any source is admitted.
- **A003 selected seeds**: `torus_3_1_direct` and `torus_3_1_hoste`;
  `uniform_s_polyline`, original `N=1200`, fixed stride=6 (200 source nodes).
- **FROZEN GRID LADDER**: `48^3`, `64^3`, `96^3` physical cube `L=12`.
  Original input file hashes are recorded. Every grid is generated separately from
  the same verified 200-node polyline; finer grids are **not interpolated 48^3 output**.
- **INITIAL GAUSSIAN CORE**: assumed **a=0.55**, Gamma=1, rho=1; not PKLSA derived.
- **Euler IVP**: genuine time evolution `du/dt=P(u x curl u)` by periodic Fourier
  incompressible RK4 with 2/3 de-aliasing, T=.02, 4 steps; no forcing/viscosity.
  This is mathematically an Euler simulation of an assumed initial field, NOT
  a new independent experimental provider or source-native PKLSA computation.
- **Independent analytic control**: Taylor-Green initial condition, time-step
  halving 4->8, energy/divergence/curl audit. This controls the *numerical solver*.
- **G41 MUST REMAIN UNRESOLVED**: the dynamics start from a Gaussian assumed
  transverse profile rather than from independently computed PKLSA finite-core
  vorticity; Euler-generated pressure is not a separate physical holdout.
- **G38/G42** are resolution/pressure *numerical diagnostics* with preregistered
  relative L2 error < 5%; FAILs are preserved. Spectral prolongation is used
  only to compare different sampled fields, NEVER to generate finer source data.
- Legacy G2/G11/G13/G24/G29/G31/G35 remain negative; do not relabel. Three
  original blind groups, their hashes/seals, and the frozen framework are never rewritten.

## Windows invocation

From `A065-v0.4.0`:

```bat
set "SST_FALSIFIER_FRAMEWORK_ROOT=C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.10"
set "SST_A003_ADAPTER_ROOT=C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A003_Fourier_Knot_Seed_Atlas\A003_Fourier_Knot_Import_Adapter_v0.2.3"
set "SST_ATLAS_ROOT=C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A003_Fourier_Knot_Seed_Atlas\A003-v0.1.2"
run_all.cmd VERIFY
run_all.cmd SELFTEST
run_all.cmd CAMPAIGN
run_all.cmd ALL
```

`CAMPAIGN` generates the three volume grids from original A003 files and solves
Euler at each grid. A standalone output PDF and JSON are always produced even
if the original atlas is missing, but missing-source gates do **not** PASS.
`ALL` additionally runs old A065 tests and an **official framework v1.0.10
FREEZE/FULL/REVEAL_IF_ALLOWED** instance (separate from portable PDF outputs).

Set `A065_V040_SAVE_FIELDS=1` if you want to export **all six** full Euler
snapshots (both `u0`, `omega0`, `p0` at t=0 and `u`, `omega`, `p` at T=0.02) as NPZ. This can take substantial disk space.
The default exports compact JSON, provenance, metrics and PDF only.

To qualify a *physical PKLSA* source, supply a second, authenticated dynamic
provider with 3D `u` or `omega`, solver/version/mesh/BC/initial data hashes,
independent pressure/velocity holdout, space/time/initial-core convergence and
strict provider independence; only a **future preregistered gate version** may
promote G41. No current gate can do that merely because numerical Euler runs.
