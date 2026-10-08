# A016 v0.2.0 — Helmholtz Vorticity-Population / Matter–Field Partition Falsifier

Framework: **SST Falsifier Framework v1.0.6**, CPU profile (Python FP64 reference + strict C++/OpenMP FP64 certification).

This release fuses the original A016 v0.1.1 Helmholtz static-centerline gates with a new population/field partition program. Scientific gate failures do **not** stop later independent scientific gates: after G0/G1/G2 prerequisites, the H* and P* branches fan out rather than forming a serial pass-only chain.

## Preserved v0.1.1 branch

- H0 closed-filament geometry / thickness precondition
- H1 resolution convergence of finite-core energy and relative-equilibrium residual
- H2 circulation/holonomy versus integer linking
- H3 relative equilibrium modulo rigid translation, rigid rotation, and tangential reparameterization
- H4 orientation/circulation reversal and mirror covariance

## Added v0.2.0 branch

- P0 exact Cauchy-map zero/nonzero vorticity-population invariance
- P1 exact incompressible material-volume conservation
- P2 exact vortex-flux conservation under stretching
- P3 exterior divergence/curl audit away from vortex support
- P4 nontrivial exterior circulation periods despite local irrotationality
- P5 nonzero kinetic-energy fraction outside a preregistered near-core source zone
- P6 far-field closed-source decay classification and post-reveal pressure-gradient exponent mapping
- B0 strict C++/OpenMP FP64 versus Python FP64 Biot-Savart parity

## Workbench placement

```text
SST-Workbench/
  01_research/A_falsifiers/A016_helmholtz_vortex_transport/A016-v0.2.0/
  06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.6/
  KnotPlot/knots/final/
```

Set `SST_WORKBENCH_ROOT` if the Workbench is not at the framework default.

## Commands

```bat
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd FULL
run_all.cmd CERTIFY
run_all.cmd REVEAL
```

Calling `run_all.cmd` without an argument defaults to `FULL` and performs `FREEZE` automatically if no frozen protocol exists.

The framework writes canonical outputs under:

```text
./helmholtz_vorticity_population_matter_field_partition_v0.2.0-outputs/
../helmholtz_vorticity_population_matter_field_partition_v0.2.0-outputs_BLIND.zip
../helmholtz_vorticity_population_matter_field_partition_v0.2.0-outputs_REVEALED.zip
```

Per-input blind metrics use HMAC-based opaque identifiers. The runtime filename map is written only under the private output subtree and is excluded from the blind ZIP.
