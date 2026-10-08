# A016 v0.2.1 validation record

Date: 2026-10-07  
Framework target: **SST Falsifier Framework v1.0.6 (`CANONICAL_FROZEN`)**
Frozen protocol bundle SHA-256: `6f5063c5091300095e3513b62fa1e0dd96940451538404399524fb6a52866a9f`

## Scope

This record validates the v0.2.1 implementation and its PKLSA cross-source architecture. It does **not** claim a scientific result from the user's real E010/PKLSA v0.4.0 atlas; that campaign must be run in SST-Workbench with the actual qualified carrier tree.

## Static/unit validation

- Framework science-contract validation: PASS.
- Framework source-contract validation: PASS.
- Framework gate-plan validation: PASS.
- Framework report completeness validation: PASS.
- Instance pytest suite: **7 passed**.
- No H0-H4 or P0-P6 scientific threshold was relaxed relative to the v0.2.0 build.
- X0 has a frozen comparison set: `H2,H3,P3,P4,P5,P6`.
- X0 closure requires at least **2** distinct upstream provider groups for a topology, at least **1** qualifying topology, and provider-state agreement `>= 0.80` for every frozen comparison gate.
- PKLSA-generated/derived carriers are evaluated but excluded from X0 closure evidence.

## Synthetic PKLSA integration smoke

A temporary mock E010/PKLSA v0.4.0 tree was created only to exercise the adapter and execution DAG. The mock release used schema `PKLSA-HIGH-RES-QUALIFICATION-4`, `atlas_version=0.4.0`, and `publication_ready_geometry_layer=true`, with one qualified topology containing two upstream provider groups plus one generated carrier.

Observed blind implementation statuses:

- G0 protocol integrity: PASS
- G1 PKLSA v0.4.0 discovery/admission: PASS
- G2 Python FP64 reference controls: PASS
- P0 Cauchy population control: PASS
- P1 incompressible material-volume control: PASS
- P2 vorticity-flux control: PASS
- H0-H4: PASS for all mock carriers
- P3-P6: PASS for all eligible mock carriers
- **X0 cross-source consistency: PASS**
- X0 closure used the two upstream provider groups; the generated carrier was excluded from the provider vote as preregistered.

This demonstrates that A016 no longer consumes only `KnotPlot/knots/final`: the runtime path is through the PKLSA release, topology qualification summaries, carrier descriptors, and resolved carrier source paths.

## Native/backend status in this build container

The synthetic integration smoke reported B0 = FAIL because `pybind11` is not installed in this restricted build container:

```text
strict C++ backend unavailable: pybind11 unavailable: No module named 'pybind11'
```

This is an environment/certification limitation, not a Python scientific-gate failure. Framework v1.0.6 keeps B0 separate from H*/P*/X0 interpretation. The Workbench `CERTIFY` run is the required native Python-FP64 versus C++/OpenMP-FP64 certification step.

## Scientific status

**REAL PKLSA v0.4.0 CAMPAIGN: NOT RUN IN THIS BUILD ENVIRONMENT.**

The prior A016-v0.1.1 results and the provisional v0.2.0 build were used only as migration/provenance inputs. They are not relabeled as v0.2.1 evidence. Run `FULL` (blind science campaign) and `CERTIFY` (including B0 native parity) against the actual SST-Workbench E010-v0.4.0 qualified atlas.
