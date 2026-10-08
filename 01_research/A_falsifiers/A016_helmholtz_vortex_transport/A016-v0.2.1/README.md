# A016 v0.2.1 — Helmholtz Vorticity-Population / Matter–Field Partition Falsifier

Framework: **SST Falsifier Framework v1.0.6 `CANONICAL_FROZEN`**, CPU profile (Python FP64 reference + strict C++/OpenMP FP64 certification).

v0.2.1 keeps the v0.2.0 science branch intact but replaces the single `KnotPlot/knots/final` input route by a **PKLSA v0.4.0 qualified-carrier interface**. It also adds **X0 — PKLSA cross-source consistency** so a conclusion cannot silently depend on one geometry provider.

## What changed from v0.2.0

- E010/PKLSA v0.4.0 is now the primary geometry/provenance layer.
- A016 requires `PKLSA-HIGH-RES-QUALIFICATION-4`, `atlas_version=0.4.0`, and `publication_ready_geometry_layer=true`.
- Only topologies with `qualification_gate_pass=true` are admitted.
- Upstream and PKLSA-generated/derived carriers are both measured, but generated carriers **cannot close X0**.
- Public blind outputs replace topology, carrier, source-family, provider, and independence identities with HMAC opaque IDs.
- Multiple carrier variants from one provider are not independent votes. They collapse to one provider state; disagreement inside one provider is `INTERNAL_INCONSISTENCY`.
- X0 compares the frozen `H2/H3/P3/P4/P5/P6` states across distinct upstream provider groups for the same blind topology.

## Scientific branches

The original A016 branch remains:

- H0 geometry/thickness
- H1 resolution convergence
- H2 holonomy/linking
- H3 relative equilibrium
- H4 reversal/mirror covariance

The v0.2.0 matter–field branch remains:

- P0 Cauchy zero/nonzero-vorticity population invariance
- P1 incompressible material-volume conservation
- P2 vortex-flux conservation under stretching
- P3 exterior divergence/curl audit
- P4 exterior circulation periods
- P5 exterior kinetic-energy fraction
- P6 far-field decay classification

v0.2.1 adds:

- **X0 PKLSA cross-source consistency**
- B0 strict C++/OpenMP FP64 parity remains unchanged

Scientific failures do **not** stop sibling scientific gates after G0/G1/G2.

## X0 rule

For one blind topology and gate `g`, each distinct upstream `provider_group` contributes at most one state:

```text
PASS | FAIL | INELIGIBLE | INTERNAL_INCONSISTENCY
```

The agreement fraction is

```text
A(T,g) = largest provider-state count / number of provider groups.
```

Frozen closure rule:

- at least **2** upstream provider groups;
- at least **1** topology satisfying that provider minimum;
- agreement `>= 0.80` for every tested `H2/H3/P3/P4/P5/P6` comparison;
- PKLSA-generated/derived carriers never count toward closure.

With two or three provider groups, this effectively requires unanimous provider classification.

## Workbench placement

```text
SST-Workbench/
  01_research/A_falsifiers/A016_helmholtz_vortex_transport/A016-v0.2.1/
  01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas/E010-v0.4.0/
  06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.6/
```

`SST_WORKBENCH_ROOT` controls the Workbench root.
A016 searches the pinned E010-v0.4.0 tree for a **unique** publication-ready `RELEASE.json`. If more than one exists it fails closed rather than choosing one by timestamp.

## Commands

```bat
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd FULL
run_all.cmd CERTIFY
run_all.cmd REVEAL
```

Calling `run_all.cmd` with no argument defaults to `FULL` and freezes the new v0.2.1 protocol first when needed.

Canonical outputs:

```text
./helmholtz_vorticity_population_matter_field_partition_v0.2.1-outputs/
../helmholtz_vorticity_population_matter_field_partition_v0.2.1-outputs_BLIND.zip
../helmholtz_vorticity_population_matter_field_partition_v0.2.1-outputs_REVEALED.zip
```

The blind package contains provider/topology group IDs but not their identities. The mapping is written under the private output subtree and appears only in the revealed package.
