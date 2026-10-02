# Einstein–SST Blind Falsifier v0.1.0

Target-free C++17/pybind11 + Python workbench for the gate order

**E3 → E4 → E5 → E2 → E1**.

The package follows the established `SST_cpp_pybind_audit_template` pattern:

- C++17/pybind11 native kernels with optional OpenMP;
- NumPy reference backend;
- native-vs-Python parity self-check;
- hash-based rebuild;
- frozen JSON configs and source hashes;
- deterministic blind seed;
- PASS / FAIL / INCONCLUSIVE / ERROR kept distinct;
- no `h`, `hbar`, `c`, `alpha`, or target value for `E/nu` / `sqrt(DeltaE/DeltaM)` in the blind evaluator;
- automatic results ZIP.

## One-click Windows runs

From `cmd.exe` in the package root:

```cmd
RUN_ALL.cmd
```

This is the recommended **standard** run and executes:

1. create `.venv`;
2. install NumPy, pybind11, setuptools and wheel;
3. build the C++17 backend (OpenMP first, automatic non-OpenMP retry);
4. strict native-vs-Python parity test;
5. run E3 → E4 → E5 → E2 → E1;
6. write a frozen manifest and one result JSON per gate;
7. create a ZIP of the complete result folder.

Alternative one-click runners (all install/build/check the native backend first):

```cmd
run_all_basic.cmd       rem quick blind campaign
run_all_standard.cmd    rem normal/recommended blind campaign
run_all_extended.cmd    rem high-resolution blind campaign
```

`RUN_ALL.cmd` is a convenience alias for `run_all_standard.cmd`. `RUN_NATIVE_SELF_CHECK.cmd` performs installation/build plus the strict C++/Python parity audit. `RUN_PYTHON_REFERENCE_QUICK.cmd` is a debugging/reference route only; it is **not** the recommended research run because it does not require the C++ backend.

## Optional relaxed-knot input

The default configs probe this path if it exists:

```text
..\..\KnotPlot\knots\final
```

External curves are currently used by E3 as additional static objectivity/translation tests. The dynamic E4/E5/E2/E1 core tests deliberately use internally generated preregistered geometries so their perturbations and mode labels are controlled.

You can override the path manually:

```cmd
.venv\Scripts\python.exe run_campaign.py --config configs\standard.json --input-root "C:\workspace\projects\SST-Workbench\KnotPlot\knots\final"
```

## Gate meanings

### E3 — Uniform-Boost / Objectivity Gate

Two identical vortex-filament states are evolved under

```text
dX/dtau = u_BS[X]
```

and

```text
dX_B/dtau = u_BS[X_B] + U
```

After subtracting the trivial `U*tau` translation, shape, localized energy, hydrodynamic impulse, curvature mode and optional imported-knot diagnostics must agree within the frozen numerical tolerance.

A FAIL falsifies the tested objectivity closure.

### E4 — Blind Action-Invariant Gate

For Kelvin-like vortex-ring excitations the code measures

```text
J_blind = DeltaE / nu
```

without loading or comparing any external action constant.

The gate requires simultaneously:

- resolved mode frequency;
- boost-objective `J_blind`;
- small coefficient of variation across amplitudes;
- log-slope of `J_blind(A)` close to zero.

A classical amplitude-squared dependence therefore fails rather than being reinterpreted post hoc.

### E5 — Symmetric Internal-Energy / Inertia Gate

This is an **operational closure test**, not a photon-emission simulation.

A standing `+m/-m` vortex-ring excitation changes localized energy `E`, fluid impulse `I_z`, and mean self-induced translation speed `U_z`. The independent inertial proxy is

```text
M_I = I_z / U_z
```

and the blind closure variable is

```text
C_blind^2 = DeltaE / DeltaM_I.
```

The evaluator does not compare `C_blind` with any known speed. A separate resolution ladder is mandatory; a relation that looks linear at one discretization but shifts beyond tolerance fails.

### E2 — Correlation / Markov Gate

A multi-mode Kelvin-ring trajectory provides an intrinsic curvature-mode phase. After removal of its coherent phase trend, the residual increments must:

- have resolved variance;
- possess a finite persistent decorrelation lag;
- exhibit an MSD exponent near one over the post-correlation range;
- satisfy a preregistered numerical-energy-drift ceiling.

Failure rejects the Brownian/Markov coarse-graining for this observable, not the underlying deterministic vortex dynamics.

### E1 — Continuum / Event-Discreteness Gate

The code constructs a fixed mode-energy proxy from continuous filament evolution, detects positive-transfer events with a preregistered MAD threshold, and fits a data-derived lattice spacing `q`.

A PASS requires:

- numerical localized-energy drift below the frozen fidelity ceiling in every event series;
- enough events in multiple amplitude series;
- stable fitted `q` across series;
- low held-out quantization residual;
- significance against matched continuous lognormal surrogates.

No `h*nu` target is available to the evaluator.

## Physical scaling

The dynamical solver is dimensionless but restored to SI with the SST canonical inputs:

```text
v_swirl = 1.09384563e6 m s^-1
r_c     = 1.40897017e-15 m
rho_f   = 7.0e-7 kg m^-3
Gamma   = 2*pi*r_c*v_swirl
```

For the default `L0 = 12 r_c`, the conversion scales are

```text
time     : L0^2 / Gamma
velocity : Gamma / L0
energy   : rho_f Gamma^2 L0
impulse  : rho_f Gamma L0^2
```

These are simulation scales, **not** blind benchmark targets.

## Numerical model

The native core uses a Rosenhead-type regularized vortex-filament Biot–Savart kernel

```text
u(X_i) = Gamma/(4*pi) Sum_j [ dX_j x (X_i-X_j) / (|X_i-X_j|^2+a^2)^(3/2) ]
```

plus RK4 time stepping. The localized filament-energy diagnostic is the consistently regularized double-line integral

```text
E = rho Gamma^2/(8*pi) int int dX . dX' / sqrt(|X-X'|^2+a^2).
```

This is a vortex-filament falsifier, not a full 3-D Euler or torsion/director-field solver. Conclusions must remain at that scope.

## Outputs

Each run creates for example

```text
results_standard_blind_20260814_012345/
  blind_manifest.json
  frozen_config.json
  physical_scale.json
  E3/result.json
  E4/result.json
  E5/result.json
  E2/result.json
  E1/result.json
  run_summary.json
```

and an adjacent ZIP with the same basename.

The `blind_manifest.json` contains the config hash, source hashes, input-curve hashes, backend, thread count, package version, and the full protocol hash.

## Interpretation rule

A numerical process exit code of zero means the campaign completed. It does **not** mean SST passed. Read `run_summary.json` and the gate-specific `verdict` fields.

`INCONCLUSIVE` is never promoted to `PASS`.
