# A058 v0.2.0 validation

## Release validation
- Instance package tests: **9 passed**.
- Exact Framework-v1.0.6 science contract validator: **PASS**, no errors.
- Exact Framework-v1.0.6 source contract validator: **PASS**, no errors.
- Exact Framework-v1.0.6 gate-plan validator: **PASS**, no errors.
- Exact Framework-v1.0.6 report validator: **PASS**, all required section markers present.
- Blind-tree simulation after nonced commitments: **PASS**, 0 forbidden-term hits.
- Full protocol FREEZE simulation using Framework-v1.0.6 protocol/blind validators: **PASS**.
- Frozen-protocol re-verification: **PASS**.

## Campaign-generation validation
A release-copy generation produced exactly **101** scientific trefoil conditions:
- BASE: 1
- S0: 33 additional conditions
- S1: 33 additional conditions
- S2: 34 conditional-force conditions

Positive ladder: `m=2^(k/4)`, `k=-16..16`; zero ladder errors. Exact `m=0` endpoints are separate. No generated scientific script overrides `fitto`, `max-dr`, `stusplit`, `close`, `dstep`, `bradius`, `cradius`, collision mode, or energy model.

Six checkpoints per condition imply **606** expected ASCII coordinate exports. A synthetic 101-condition/606-checkpoint analysis simulation completed successfully, including zero-equivalence, local response, reciprocal-asymmetry and quadratic-fit paths.

## Install integration-test contract
`run_install.cmd` runs package tests and then `run_install_export_test.cmd`. The integration test launches KnotPlot once, performs `reset all`, loads catalogue `3.1`, refines to 300 beads, prints runtime parameter state, writes exactly **one** ASCII trefoil coordinate file, verifies it is parseable, and performs **no relaxation iterations**.

## Native backend
The C++17/pybind11 source is retained from the successfully used A058 metric kernel and is compiled by `run_install.cmd` before tests. A native link was not repeated in this sandbox because a complete pybind11 installation was unavailable offline; no prebuilt binary is shipped.
