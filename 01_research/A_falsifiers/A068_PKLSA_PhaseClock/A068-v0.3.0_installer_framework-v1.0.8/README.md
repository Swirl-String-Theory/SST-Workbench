# A068 PKLSA Phase Clock — v0.3.0 / SST Falsifier Framework 1.0.8

**New separate instance, never patch A068 v0.2.0 or the v1.0.8 framework.**

**Evidence class:** `NUMERICAL_EULER_MODEL_DIAGNOSTIC_ONLY` / not experimentally validated, not source-independent PKLSA physical dynamics. G3 physical clock `UNRESOLVED`. This version carries a byte-identical upstream A064 Euler solver and a genuinely evolved 3D flow initialized from native KnotPlot trefoil `knot_3.1.txt`.

## Install in the existing Windows SST-Workbench

Required official local framework: `C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.8` (must contain `tools\new_falsifier.py` and `instance_template`). Keep v1.0.7 canonical frozen parent untouched. The framework v1.0.8 release is a local validated **candidate**, not hardware-certified on your PC.

Extract this ZIP to an arbitrary folder and run:

```cmd
py -3 install_A068_v0.3.0.py --workbench-root C:\workspace\projects\SST-Workbench
```

The installer invokes the official v1.0.8 instance generator, then overlays science code, fixed inputs and contracts. It **refuses to overwrite** any existing `01_research\A_falsifiers\A068_PKLSA_PhaseClock\A068-v0.3.0` target and verifies the `.sst_framework_root` relative pin. It preserves generated private HMAC/nonce material. The old `A068-v0.2.0` and all historic results remain unchanged.

Before FREEZE ensure protocol, data, private mapping and gate definitions are consistent. No scientific contract may be changed after `FREEZE`; any change requires a new version.

```cmd
cd C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A068_PKLSA_PhaseClock\A068-v0.3.0
python -m pytest -q tests
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd FULL
run_all.cmd CERTIFY
run_all.cmd REVEAL_IF_ALLOWED
```

Do **not** repeatedly run `CERTIFY` hoping G3 will pass. v1.0.8 creates a new run ID for every blind BASIC/FULL/CERTIFY execution and archives the prior output directory non-destructively. FULL and CERTIFY recompute separately; they do not add their gate results together.

## Numerical dynamics

No prescribed signal or frequency is injected. Actual computation:

1. Read hash-locked original 47-point KnotPlot XYZ. The topology label is not independently certified, and this is not a qualified PKLSA eigenstate.
2. Use original A064 `normalized_components`, deposit signed line current on periodic 3D grid, Gaussian finite-core smooth and solenoidal Fourier Biot–Savart initialization with `gamma=1`, `L=2*pi` dimensionless.
3. Evolve 3D unforced incompressible Euler with 2/3 Fourier truncation and RK4, no clock law.
4. Save actual time-dependent `u(t,x,y,z)` with `t`, `domain_length`, dimensionless shape signals, energy/helicity/enstrophy, divergence and CFL to `EULER_3D_FIELDS_MODEL_ONLY.npz`; write results and full five-branch screens to `EULER_DYNAMICS_RESULTS.json`.
5. Compute rotation-invariant enstrophy-covariance shape gap q_shape plus a distinct full-box normalized enstrophy/energy ratio qZ = L^2 Z/E. Run Hilbert phase screens. q_shape and qZ are distinct measurements of **the same** simulated flow, not source independence.
6. For FULL/CERTIFY compare fixed final T=20 with n16 dt=.04; n24 dt=.04; n16 dt=.02; n16 core=.32; n16 core=.48.

BASIC: n=16, T=6, dt=.04, 151 3D snapshots. FULL/CERTIFY: n=16, T=20, dt=.04, 251 snapshots plus four refinement/parameter branches. All times, distances and frequencies remain in **dimensionless numerical units**.

## Existing local exploratory precheck (not an official framework run)

17/17 instance regressions PASS on the author's local model environment (unit and pipeline tests). Five FULL numerical Euler evolutions were run before distribution. The primary numerical model passes conservation/divergence/CFL gates, but the phase candidate shows ~0.646 cycles rather than preregistered >=6 cycles, and grid/core refinement is poor:

| branch | N | core | dt | final Z |
|---|---:|---:|---:|---:|
| base | 16 | .40 | .04 | .06420168468 |
| mesh | 24 | .40 | .04 | .12169720003 |
| dt/2 | 16 | .40 | .02 | .06420168455 |
| core-low | 16 | .32 | .04 | .09474986421 |
| core-high | 16 | .48 | .04 | .03564238913 |

Temporal relative enstrophy error 2.01e-9 PASS; spatial relative error .47245 SCREEN_FAIL; core relative spread .92065 SCREEN_FAIL. This is a **nonconverged physical-source model**, not evidence that SST as a whole is false.

## Framework gate interpretation

- G0/G1: official freeze and source hashes.
- G2: actual numerically evolved 3D incompressible Euler conserved to screen tolerances; `PASS` is numerical only.
- G3: physical clock `UNRESOLVED`: material tube, relative periodic orbit and independent PKLSA source not supplied. Even a calculated model Hilbert frequency could not close physical G3 by itself.
- G4–G8: skipped if G3 unresolved; required withheld Floquet, space/time/core qualification, native backend and provider independence not faked.
- G9: reveal only when v1.0.8 frozen nonced commitments and blind scientific gate requirements succeed. `REVEAL_IF_ALLOWED` is expected to be withheld with the present inputs.

## Known limits and next essential inputs

The PKLSA KnotPlot carrier geometry is a geometric **initial condition**, not independent source-native material vortex dynamics; downstream A064 numerical propagation does not validate a physical Kelvin eigenmode. To test a physical clock, the next version needs: (a) independent source-native calibrated 3D `u(x,t)` and core metadata; (b) tracked 3D material tube surface; (c) a full-field symmetry-reduced relative-periodic-orbit calculation; (d) an independently calculated Euler/Floquet frequency on a withheld branch; (e) spatial, temporal and finite-core convergence on the same state; (f) genuinely independent providers. The current v0.3.0 archive and PDF make these unresolved qualifications explicit.

## Package layout

- `install_A068_v0.3.0.py` : idempotence-safe installation using **official** v1.0.8 generator.
- `overlay/experiment/dynamics.py` : 3D nonlinear Euler trajectories and dimensionless clock observables.
- `overlay/experiment/euler3d.py` : original byte-exact A064 3D Euler source for provenance.
- `overlay/experiment/phaseclock.py` : preflight phase estimator.
- `overlay/experiment/pipeline.py` : frozen framework gate integration.
- `overlay/data/` : KnotPlot XYZ and hashed historical A064/A068 controls, plus explicitly labeled development summary (not a new independent dataset).
- `overlay/report/FALSIFIER_REPORT.tex` : complete mathematics, inference limits and per-run automatic ledger placeholders.
- `overlay/tests/` : deterministic regressions.
- `FALSIFIER_REPORT_PREVIEW.pdf` : 5-page compiled science/protocol preview, **not** a framework-certified run report.

The optional separate results download contains `EULER_3D_FIELDS_MODEL_ONLY.npz` and JSON from the independent local FULL simulation; these were not generated via v1.0.8 FREEZE/CERTIFY in this environment. On Windows, the official framework run reproduces and records its own authoritative per-run evidence with unique run IDs.
