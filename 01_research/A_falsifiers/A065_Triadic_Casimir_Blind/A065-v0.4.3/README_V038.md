# A065-v0.3.8 — Source-Native Vorticity Core Closure (preparatory)

**Scientific status: NOT CERTIFIED AS PKLSA EULER.**

This extends genuine A065-v0.3.7 files without changing frozen SST Falsifier Framework v1.0.7, three sealed datasets, historical failures or native numerical kernels. Current 3D `omega,u,p` sample volumes are **synthetic**: they come from Gaussian smoothing a historical 2015 parametric trefoil with an explicitly prescribed input width. The data demonstrate that the field-based falsifier is executable; they cannot demonstrate an emergent physical SST core.

## Run under Windows (Python >= 3.10)

```bat
py -3 -m pip install -r requirements.txt
run_all.cmd VERIFY
run_all.cmd CORE3D
run_all.cmd SELFTEST
run_all.cmd ALL
```

`CORE3D` runs quickly, produces `CORE3D_{FOURIER_A,TORUS_B}_V038.npz` volumes of shape `(3,48,48,48)` and other numerical fields `u,p`, `SOURCE_NATIVE_CORE_V038_RESULT.json`, an explicit PDF and a LaTeX report in unique `exports/<RUN_ID>/` and `runs/<RUN_ID>/`. The runner never overwrites a previous run.

`ALL` also triggers all older A065 tests, authentic historical C++17 backends and optional official SST Falsifier Framework v1.0.7 via `SST_FALSIFIER_FRAMEWORK_ROOT`. G28-G32 appear in the framework instance gate plan. **G32 cannot PASS yet**; it requires true 3D dynamic PKLSA fields and an independent heldout provider. The synthetic G31 failures are not claims about physical SST.

To audit a future *authentic* dynamic provider's metadata only:

```bat
run_all.cmd CORE3D_IMPORT C:\path\native_omega.npz C:\path\native_omega_manifest.json
```

This is **not** source certification. Audit the original solver, finite-volume/midpoint pressure boundary condition, 3D field resolution, time/core convergence, circulation/enstrophy budgets and independent heldout u/p provider before any physical gate promotion.

## Architecture

- `triadic/native_core_v038.py`: source-classified synthetic 3D omega, periodic velocity Helmholtz projection, pressure-Poisson diagnostic, local tangent/normal sections, Gamma/Z inverse and no-fit heldout tests.
- `triadic/native_core_report_v038.py`: PDF+LaTeX report.
- `preregistration/SOURCE_NATIVE_CORE_V038.json`: predeclared source hashes and numerical criteria.
- `imports/PKLSA_3D_SNAPSHOT_SCHEMA.md`: actual PKLSA provider interface.
- `docs/SOURCE_NATIVE_CORE_V038_CONTRACT.md`: science contract, gates, limitations.
- `tests/test_v038_core3d.py`: fast numerical and source-security tests.

**Important:** The periodic FFT pressure field is not a separately measured pressure distribution, and a steady Euler momentum residual is explicitly reported. No SI SST calibration is applied.

### If your PKLSA solver exports velocity but not omega

The supplied `tools/convert_native_velocity_v038.py` can reconstruct vorticity using a spectral curl *only for periodic grids*. It never guesses boundary conditions and preserves hashes:

```bat
py -3 tools\convert_native_velocity_v038.py --velocity C:\data\pklsa_velocity.npy --upstream-manifest C:\data\pklsa_velocity_manifest.json --output C:\data\pklsa_omega_from_u.npz
```

The upstream manifest must declare `schema`, `source_sha256`, `provider`, `solver_commit`, `run_id`, `time`, `units`, `dx`, and `boundary_conditions="periodic"`. It cannot replace an external Euler solver or independent heldout pressure provider.
