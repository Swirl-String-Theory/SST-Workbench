# Validation — v0.1.1

Validation date: 2026-08-22.

## Release checks

- Python regression suite: **16/16 PASS** (`pytest`).
- Python bytecode compile (`compileall`): **PASS**.
- JSON configuration parse: **8/8 PASS**.
- Symmetric closure algebra regression: **PASS** (`(k_-+k_+)/2 = k_0`).
- Neutral/neutral growth tie regression: **PASS**.
- Swirl-Clock profile metrics regression: **PASS**.
- New-carrier catalog regression: **PASS** for `T(3,4)` and `T(3,5)` plus the four other confirmatory carriers.
- Dynamics-source invariant: **PASS**. `confirmatory_phase_target` does not occur in `analyze.py`, `eigen.py`, `delay.py`, or `workflow.py`; no `tau_delay`, `feedback_delay`, or `user_delay` appears there.
- Preregistered target-phase carrier sign-test unit regression: **PASS**, 6/6 synthetic directional votes gives exact one-sided p = `1/64`.
- C++17 pybind11 syntax compile: **PASS**.
- Temporary native module load: **PASS**, backend reported `cpp-pybind11`.
- Native geometry helper smoke: **PASS**.
- Native blind protocol smoke: **PASS** (`prepare -> blind -> SHA-256 seal -> reveal`).
- Source-only fallback regression after deleting temporary native binary: **16/16 PASS**.
- UTF-8 report I/O: **PASS**.

## Native source continuity

`cpp/native.cpp` is byte-identical to the already validated v0.1.0 kernel:

```text
sha256 9c0b0bee4dab1295d045fa8e2479c7e7b0199fc627c960509c50382fd1cf91c2
```

The local audit compiled and loaded the helper as a Python extension. The temporary Linux binary is deliberately excluded from the release. On Windows, `run_01_build_native.cmd` builds the C++17/OpenMP `.pyd` with the installed pybind11 headers and VS2022/MSVC.

## Fresh v0.1.1 native end-to-end smoke

A two-pair reduced-resolution campaign was run with the temporary native helper loaded. Blind output reported:

- backend: `cpp-pybind11`;
- `SST-FINITE-CORE-BLIND-1.1`;
- symmetric control enabled;
- carrier identity unread;
- condition identity unread;
- explicit delay parameter unused;
- target phase unused in dynamics;
- result tree sealed before reveal.

The reveal reported:

- valid-only median group-delay vs wave-packet-return relative error: `0.0075`;
- self-generated delay gate: **PASS**;
- CLOSED / symmetric-control median growth ratio near unity in this smoke;
- overall verdict: `MECHANISM_NOT_ESTABLISHED`.

This is the desired falsifier behavior: a accurately measured propagation delay does not automatically create a phase-feedback stability PASS.

## Prepared campaign sizes

| preset | blind pairs | anonymous candidates |
|---|---:|---:|
| basic | 8 | 16 |
| extended | 96 | 192 |
| profile robustness | 72 | 144 |
| core radius | 48 | 96 |
| chirality/sign | 120 | 240 |
| radial convergence | 16 | 32 |
| **Swirl Clock m=1 confirmatory** | **144** | **288** |
| **Swirl Clock m=2 control** | **144** | **288** |

## Methodological fixes verified

### Both-valid scoring

Carrier closure votes are constructed only from pairs satisfying

```text
closed_mode_valid == true
control_mode_valid == true
neutral_pair == false
```

so an invalid control cannot generate an apparent closure advantage.

### Symmetric closure control

For a preregistered closure offset magnitude \(\delta\), the control evaluates both \(n-\delta\) and \(n+\delta\), and averages their growth metrics. This cancels the first-order local \(dg/dk\) bias.

### Valid-only delay aggregate

The reveal delay statistic uses only CLOSED rows satisfying both the finite-core mode gate and successful wave-packet-return measurement.

### Swirl Clock export

`SWIRL_CLOCK.csv` is generated at reveal and includes

```text
lambda_real
lambda_imag
omega_mode
T_mode
group_velocity
tau_loop_group
tau_return_measured
phi_loop
omega_swirl_rms_core
mode_over_swirl_frequency_ratio
```

## Scientific scope

v0.1.1 remains a **slender finite-core linear incompressible-Euler mechanism falsifier**. The local core eigenproblem is finite-core and radially resolved; global knot geometry enters through length, curvature validity and Bishop holonomy. It is not yet a full curved-core 3-D Euler/Floquet or nonlinear orbital-stability solver.
