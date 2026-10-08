# A016 v0.2.2 validation record

## Scope

This record validates the v0.2.2 source-handoff repair and the unchanged A016 Helmholtz/Cauchy + H0-H4/P3-P6/X0 execution architecture under SST Falsifier Framework v1.0.6. It does not relabel the synthetic integration campaign as scientific evidence from the user's real Workbench.

The repair is driven by the actual Workbench pipeline: E010-v0.3.1 is the parent geometry/source/topology qualification layer, while E011-v0.3.0 is the falsifier-facing `STATIC_READY` seed atlas. E010's global `publication_ready_geometry_layer=false` and `full_campaign_gate_pass=false` are therefore recorded but are not promoted to an automatic rejection of the independently admitted E011 subset.

## Static validation

- Framework `validate_instance.py`: **PASS**.
- Unit/integration tests: **8 passed**.
- Frozen protocol bundle SHA-256: `192a9159e6d27a45247293217e713afeda4be8f2956a0f6ec2ae69df0f8ba27f`.
- Frozen framework target: SST Falsifier Framework v1.0.6.
- Supported E011 upstream representations: `gilbert_ab_record`, `vect`, `xyz`.
- Unknown representations fail closed.

## Actual Workbench-shape adapter checks

The adapter was checked against the real E011-v0.3.0 manifests retrieved from the user's Workbench copy:

- `STATIC_READY_PROVIDER_ANCHORS.jsonl`: 47 records; representations = 33 `gilbert_ab_record`, 8 `vect`, 6 `xyz`; providers = 33 Gilbert, 14 KnotPlot; 34 topologies.
- `STATIC_READY_PRIMARY_SEEDS.jsonl`: 431 records; representations = 33 `gilbert_ab_record`, 155 `vect`, 243 `xyz`; providers = 33 Gilbert, 398 KnotPlot; 34 topologies.

Three real source-format specimens were also exercised directly:

- Gilbert `Ideal.txt.gz`: raw SHA-256 `274a4ce111607a6295e280f3f8369c665e7de82ac33afcd4cb227eb61568d530`; record `3:1:1` resolved and sampled to 4096 points.
- KnotPlot VECT `knot_3.1_trial_001k_rr_010k_coarse.final.vect`: raw SHA-256 `8fea8a15ff3047dbbfb4aba05090b9a6cadc10eeedf97c22350925c764bc540e`; parsed as one 300-point component.
- KnotPlot XYZ `knot_3.1_trial_008k.txt`: raw SHA-256 `f87fd7a08fb254c93941ff59c8a29762adfadefe1df8c74889a6460c4a5c4be5`; parsed as one 300-point component.

These hashes match the corresponding E011 source locators used for the adapter audit.

## Synthetic end-to-end regression

A temporary E011-shaped Workbench fixture was used only to exercise orchestration. Its E011 summary had `execution_gate=PASS`, while its E010 parent deliberately had both `publication_ready_geometry_layer=false` and `full_campaign_gate_pass=false`. Two independent upstream providers for one topology were supplied.

`tools/preflight_e011.py BASIC` reported:

- E011 v0.3.0: **PASS**;
- E010 parent v0.3.1: resolved;
- admitted carriers: 2;
- distinct topologies: 1;
- multi-provider topologies: 1.

The frozen BASIC pipeline then produced:

- G0/G1/G2: **PASS**;
- P0/P1/P2: **PASS**;
- H0-H4: **PASS** on the synthetic controls;
- P3-P6: **PASS** on the synthetic controls;
- X0: **PASS**, with two provider votes and agreement fraction 1.0 for H2/H3/P3/P4/P5/P6;
- no source/sample errors.

For the synthetic closed-source controls, P6 returned velocity exponents approximately 3.00210, corresponding under the post-fit steady Bernoulli exponent map to pressure-gradient exponents approximately 7.0042. These values are smoke-test outputs, not physical evidence.

## Backend certification in this container

B0 is **not certified in this Linux build environment** because `pybind11` is absent. The pipeline correctly reports a strict backend failure rather than accepting a Python fallback. The user's prior Windows A016 v0.2.1 execution already demonstrated that the instance-local OpenMP FP64 backend can build and certify on the Workbench host; v0.2.2 must still rerun B0 because its native source/version fingerprint is a new release artifact.

## Real campaign status

**REAL E011-v0.3.0 A016 CAMPAIGN: NOT RUN IN THIS BUILD ENVIRONMENT.**

The user's Workbench should run the frozen v0.2.2 release against the existing E011-v0.3.0 `STATIC_READY` outputs and raw source tree. Recommended order:

```bat
run_all.cmd SELFTEST
run_all.cmd BASIC
run_all.cmd FULL
run_all.cmd CERTIFY
```

`run_all.cmd` now performs an E011 preflight before BASIC/FULL/CERTIFY and fails early with an actionable diagnostic if the required atlas, parent contract, seed manifests, raw source files, or hashes cannot be resolved.
