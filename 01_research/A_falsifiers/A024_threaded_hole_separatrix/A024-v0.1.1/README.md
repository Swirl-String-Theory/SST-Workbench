# SST Threaded-Hole Substrate Blind Falsifier v0.1.1

Purpose: test whether a **self-consistent bundle of closed vortex threads through a carrier's central hole** can (a) improve dynamical self-confinement and (b) generate a coarse-grained pressure deficit with a Newton-like far profile, without external cylinder rotation, damping, mutual friction, or a hard-coded gravity law.

## v0.1.1 Windows UTF-8 hotfix

All Python text reports/config/seal reads and writes use explicit UTF-8. `_common.cmd` also enables Python UTF-8 mode. This fixes CP1252 `UnicodeEncodeError` failures when reveal reports contain symbols such as `Δ` and `²`. Physics and blind scoring are unchanged.

**Recovering an already-sealed v0.1.0 basic run:** do not modify or replace files in the sealed v0.1.0 project before reveal. From that existing project directory run:

```cmd
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
run_basic_reveal.cmd
```

This changes only the Python process encoding and therefore preserves the v0.1.0 code hash. Use v0.1.1 for new campaigns.

## Carrier strata

- analytic torus knots: `T(2,3)`, `T(2,5)`, `T(2,7)`, `T(2,9)`;
- twist / near-unknot-with-twist: Fremlin `4_1`, `5_2`, `6_1`, `7_2`;
- `TRIPLE_GEAR_T3_3`: analytic `T(3,3)` three-component torus-link proxy. Each carrier component is an unknot; the three components share a central toroidal hole. It is a topology/geometry proxy for the mechanical triple gear, **not** a tooth/contact mechanics simulation.

## Thread sector

Every background thread is a **closed vortex loop**. One leg passes helically through the central hole; a far return leg closes the loop. There are no vortex endpoints.

The paired null case contains the *identical thread geometry* with exactly zero thread circulation. The active candidate has

\[
\Gamma_B = \frac{\beta\,\Gamma_K}{N_B},
\qquad
\beta=\frac{N_B\Gamma_B}{\Gamma_K}.
\]

Thus geometry/component count do not change between active and null.

## Blind gates

`G0` source/hole/thread qualification and sealed anonymization.

`G1` carrier self-confinement: contact survival, relative-equilibrium residual, shape AUC/RPO residual.

`G2` restoring modes: finite-difference Kelvin/Fourier Jacobian and maximum real growth rate.

`G3` pressure-Poisson: reconstruct

\[
\nabla^2 p=-\rho\,\partial_i v_j\partial_j v_i
\]

on a coarse grid and test whether active threading makes the central pressure more negative.

`G4` far-profile falsifier: independently fit spherical coarse-grained pressure to `A+B/r` and `A+C/r^2`; report which fit wins. No `1/r` profile is imposed.

`G5` circulation-similarity: at fixed `beta`, geometry and core ratio, pure Euler/Biot-Savart trajectories should collapse under `tau=|Gamma_K| t`. A strong absolute-Gamma dependence is treated as numerical/model contamination, not new physics.

## One-click runs

```cmd
run_all.cmd
run_all_extended.cmd
run_all_torus.cmd
run_all_twist.cmd
run_all_triple_gear.cmd
run_all_similarity.cmd
run_all_density_helix.cmd
```

All production extended/family runs require the C++17/pybind11 backend. Default OpenMP thread count is 16.

## Blind architecture

`prepare` writes anonymous `CAND_*` geometries and shuffled `PAIR_*` rows. Carrier identity, family, active/null condition, beta, thread density, source and link matrix remain in `outputs/<campaign>/campaign/private/`.

`blind` cannot read that directory. It seals code, config, public anonymous catalog and results with SHA-256.

`reveal` refuses changed code/results/catalog/private commitments, then joins identities and reports separate self-confinement, pressure and far-field verdicts.

## Interpretation guard

A central pressure deficit is **not** by itself a gravity derivation. Gravity closure survives only if the independent far-profile gate also favors `1/r` over `1/r^2`, and even that remains a reduced filament/coarse-grid result requiring larger-domain convergence.
