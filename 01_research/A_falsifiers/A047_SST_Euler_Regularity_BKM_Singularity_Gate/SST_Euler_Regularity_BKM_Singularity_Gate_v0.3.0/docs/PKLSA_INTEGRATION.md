# E010 / PKLSA v0.3.1 integration — A047 v0.3.0

A047 v0.3.0 consumes the repository-native **E010 SST Parametric Knot-Link Seed Atlas v0.3.1** production result rather than the historical self-contained PKLSA v0.1.1 `families/14_knot_3p1.npz` bundle.

## Authority boundary

Runtime authority is:

1. `E010-v0.3.1/E010_PKLSA_Production_Knot_Link_Basis_v0.3.1-outputs/RELEASE.json`;
2. `poc/atlas/3_1/qualification/summary.json`;
3. `source_independence.json` and `geometry_metrics.json`;
4. the per-carrier `CAR_*.json` envelopes under `sources/` and `generated/`;
5. the original source bytes referenced by each carrier.

The copied `data/E010_v0.3.1_3_1_POC_SNAPSHOT.json` is documentation only and never admits a scientific case.

## Fail-closed checks

Before Euler evolution A047 requires E010 v0.3.1 source-native mode and the source-contract, A001--A008 coverage, canonical-identity, identity-database, topology-database and trefoil-POC gates to be green. It deliberately does **not** require E010's all-topology `full_campaign_gate_pass`, because A047 consumes only the separately qualified `3_1` POC.

Every admitted carrier is reloaded from the current Workbench source tree. A047 checks the carrier `raw_sha256` and recomputes the exact `PKLSA-GEOMETRY-SHA256-v1` geometry digest. A moved Workbench root is supported by remapping the recorded path suffix after `SST-Workbench/`.

## Default scientific selection

The default BASIC campaign:

- removes E010 literature-hard-gate failures (`G1/G2/G3`);
- removes `BYTE_IDENTICAL_MIRROR_NOT_INDEPENDENT` and `MIRROR_NOT_INDEPENDENT` evidence classes;
- removes recorded geometry/raw duplicates;
- retains the remaining source-native trefoil shape population across source families;
- hashes carrier and independence-group identities before writing BLIND output.

In the production output inspected on 2026-09-28 this maps 189 qualified trefoil carriers to 116 default A047 geometries. This count is not hard-coded at runtime.

## Loader contract

A047 imports the exact `pklsa_builder.io_geometry` and `pklsa_builder.gilbert` loaders from the local E010-v0.3.1 source tree. This avoids reimplementing E010's VECT/Fourier/Gilbert/XYZ format semantics inside the falsifier.

## Independence guard

An E010 `independence_group` is a stratification/provenance label, not a replication count. BKM convergence is computed only over repeated `(N, dt)` runs of the **same centerline**. Different carriers, even within the same source family, can never be pooled to manufacture a converged singularity candidate.
