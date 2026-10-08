# A016 v0.2.0 validation record

Date: 2026-10-07
Framework target: SST Falsifier Framework v1.0.6 (`CANONICAL_FROZEN`)
Protocol bundle SHA-256: `17158e263151546885b66290e74ba6f0a6fbb456c6a3303dc0141545b20c586c`

## Static validation

- `science_contract.json`, `source_contract.json`, `gate_plan.json`, blind policy, and report passed Framework v1.0.6 freeze validation.
- Frozen protocol created successfully.
- Instance tests: **3 passed**.
- No placeholder tokens remain in frozen scientific contracts/report.
- Public source tree contains none of the configured forbidden target terms.

## Synthetic end-to-end smoke validation

A temporary three-geometry source directory (circle, trefoil-like parametric control, figure-eight-like parametric control) was used only to validate execution. It is **not** part of the packaged scientific evidence.

Observed implementation-validation statuses:

- G0, G1, G2: PASS
- P0 Cauchy population: PASS; relative error `0.0`
- P1 volume/Jacobian: PASS; `det(F)=1.0`
- P2 vorticity flux: PASS; relative drift `0.0`
- H0, H1, H2, H4: PASS on all 3 controls
- H3 relative equilibrium: **FAIL on 2/3 controls**
- P3, P4, P5, P6: PASS on all eligible controls **despite the earlier H3 failure**
- B0 C++/OpenMP FP64 certification: PASS; Python/C++ relative L2 `8.44323803752299e-16` against tolerance `1e-10`

The last two points validate the intended continue-after-scientific-failure fan-out semantics and the strict native certification lane.

For the synthetic closed sources, the P6 validation fitted velocity exponents approximately `3.0007--3.0021`, producing the mechanically derived steady-Bernoulli pressure-gradient exponent approximately `7.0013--7.0042`. These are implementation controls, not results from the Workbench knot library.

## Scientific validation status

**UNRUN ON THE USER'S ACTUAL `KnotPlot/knots/final` SOURCE IN THIS BUILD ENVIRONMENT.**

The supplied v0.1.1 frozen outputs were analyzed for migration, but v0.2.0 deliberately does not reclassify those historical outcomes as new v0.2.0 results. Run `FULL` or `CERTIFY` in SST-Workbench to produce the new blind campaign.
