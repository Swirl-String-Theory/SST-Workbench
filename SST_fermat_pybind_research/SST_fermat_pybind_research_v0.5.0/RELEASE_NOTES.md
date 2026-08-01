# Release notes — v0.5.0

v0.5.0 adds full three-dimensional Fermat ray integration, closed-orbit shooting, two-axis orbit convergence, and reduced monodromy diagnostics on top of the v0.4.3 local-candidate harness.

## New research modules

- `fermat_ext/geodesic.py`
- `run_geodesic_shooting.py`
- `run_orbit_convergence.py`
- `run_monodromy.py`
- `run_global_orbit_campaign.py`

## Certification hierarchy

A single shooting solution is not called globally certified. The global flag requires both ray-step convergence and centerline-resolution convergence. Monodromy certification additionally requires perturbation-scale convergence and a globally certified orbit.

`qsm_certified` remains `false`: no wave or complex-frequency pole solver is included.

## Local validation result

The Python-fallback smoke campaign completed all four pipeline stages. Its low-resolution `0_1` seed did not resolve a closed orbit, which is a valid scientific result and confirms that campaign success is separated from positive orbit certification. Native Windows certification must be performed with `START_V050_GLOBAL_ORBIT_SMOKE.bat` and then the full campaign.
