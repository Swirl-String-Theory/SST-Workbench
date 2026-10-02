# E011 SKLSA — Selected Literature-Gated Carrier Atlas v0.2.0

E011-v0.2.0 is the downstream selected knot/link atlas for the completed **E010-v0.3.1** qualification run. It deliberately avoids re-processing all 2227 E010 topologies and never treats a directory or filename as evidence that a carrier is valid.

## Parent contract

E010 remains authoritative for source discovery, representation parsing, provenance, mirror reconciliation, topology identity, numerical convergence and the v0.3.1 literature gates. E011 reads the qualification ledgers produced by E010 and classifies each requested topology independently.

A crucial v0.2.0 rule is that E011 does **not** require the whole E010-v0.3.1 campaign to be green. The v0.3.1 literature gates are intentionally stricter and can exclude many of the 2227 topologies. E011 therefore accepts a structurally valid v0.3.1 parent, then admits only selected topologies whose own E010 gates are green.

For every selected topology, E011 first requires a valid E010 identity result. It then applies the hard literature gates **per carrier**. A topology is admitted when identity passes and at least one carrier survives G1/G2/G3. Aggregate E010 topology failure is preserved as context, because E010 publication mode can fail a whole topology when only a subset of its carriers fail.

Carriers that fail G1/G2/G3 remain in the E011 audit output but never enter provider representatives or metric consensus. If no carrier survives, the topology is excluded.

## Selected scope

Default `selected` mode contains the original SKLSA set:

- all 35 prime knots from 3 through 8 crossings;
- `L2a1`, `L4a1`, `L5a1`, `L6a1`–`L6a5`, `L6n1`, `L8a1`;
- optional sentinels `9_1`, `9_2`, `10_1`, `11_1`, `11_2` only with `--include-sentinels`.

The selection is a research/data-reduction policy, not a physics claim.

## Carrier handling

E011 consumes E010's `source_matrix.csv`, `source_independence_ledger.json`, `geometry_metrics.json` and `convergence.json`.

- byte-identical and declared mirrors remain visible for provenance but do not create independent evidence;
- generated/control families stay labelled as generated or derived;
- only carriers with `literature_hard_gate_pass == true` can become provider representatives;
- provider representative choice is deterministic data reduction, **not** a physical best-seed score;
- if only literature-passing mirrors remain, E011 may emit one `mirror_fallback_provenance_only` geometry representative; it is never counted as independent evidence and never enters consensus;
- `Wr` and `|Wr|` are kept separately so orientation reversal is not silently treated as geometric disagreement.

### The `8_5` exception

`8_5` had the historical Fremlin/header repair. E011 does not special-case the whole Fremlin family because of it. It simply consumes the repaired E010-v0.3.1 carrier records and their mirror/independence classification. Thus the exceptional file cannot become a family-wide assumption.

## Run

From the E011-v0.2.0 directory:

```bat
run_all.cmd C:\workspace\projects\SST-Workbench
```

POC subset:

```bat
run_poc.cmd C:\workspace\projects\SST-Workbench
```

For audit/reproduction, the Python runner also accepts the E010 output ZIP directly:

```bat
python tools\run_analysis.py   --workbench-root C:\workspace\projects\SST-Workbench   --e010-output C:\workspace\projects\SST-Workbench\01_research\E_pipelines\E010_pklsa_parametric_knot_link_seed_atlas\E010-v0.3.1\E010_PKLSA_Production_Knot_Link_Basis_v0.3.1-outputs.zip
```

When a ZIP is supplied, E011 extracts only root ledgers plus qualification artifacts for the requested SKLSA topologies and records the parent ZIP SHA-256.

## Outputs

- `RUN_SUMMARY.json`
- `PARENT_RELEASE.json`
- `PARENT_INPUT.json`
- `PARENT_WARNINGS.json`
- `SELECTION.json`
- `E010_ADMISSION_MATRIX.json/.csv`
- `TOPOLOGY_SUMMARIES.json`
- `OPERATIONAL_ERRORS.json`
- `CARRIER_AVAILABILITY.csv`
- `E010_CARRIERS.jsonl`
- `ADMITTED_CARRIERS.jsonl`
- `PROVIDER_REPRESENTATIVES.jsonl`
- `METRIC_CONSENSUS.csv`
- `PAIRWISE_METRIC_DELTAS.csv`
- `topologies/<ID>/...`

Two statuses are deliberately separate:

- `execution_gate`: whether E011 successfully classified every requested topology without missing/corrupt parent artifacts;
- `atlas_status`: `COMPLETE` or `PARTIAL_CARRIER_ADMISSION`, reflecting whether every selected topology retained at least one literature-admitted carrier.

A partial atlas is therefore a valid result, not a software failure.

## Boundary

E011-v0.2.0 is a geometry/source comparison and selection layer. It does not establish Euler/Biot–Savart stability, Kelvin/Floquet stability, particle identity, or any SST physical claim.