# E010 — SST Parametric Knot-Link Seed Atlas v0.3.0

Repository-native PKLSA release for the restructured `SST-Workbench`.

This release is both:

1. an installable Python façade (`sst_pklsa`) for resolving and inspecting the Workbench knot evidence graph; and
2. the high-resolution geometry qualification pipeline inherited from the v0.3.0 qualification builder.

It **does not copy the full knot datasets** into the release. Raw bytes remain in `03_data`; PKLSA records paths, hashes, source roles, lineages, topology references and qualification results.

## Why this release exists

The restructured Workbench now separates:

- raw/reference data under `03_data/A_knots`;
- generated data under `03_data/D_generated`;
- reusable knot code under `02_libraries/A_knot_libraries`;
- producer tools under `04_tools`;
- research producers such as PTSA/QHP/KAtlas conditioning under `01_research/E_pipelines`.

PKLSA v0.3.0 resolves those layers without flattening them into one pseudo-independent dataset.

## Public Python API

```python
from sst_pklsa import Workbench

wb = Workbench.open(r"C:\workspace\projects\SST-Workbench")
print(wb.doctor()["coverage"])

carriers = wb.discover_carriers("3_1")
for c in carriers[:10]:
    print(c.source_family, c.carrier_id, c.independence_group)
```

The core does not require either existing `sst_knotlib` implementation to be imported. This is deliberate: the current Geometry Library and Knot Library both contain a top-level `sst_knotlib` package, so blindly putting both providers on one `PYTHONPATH` is ambiguous. `sst_pklsa bridges` reports that condition instead of silently selecting one.

## Commands

```bat
python -m sst_pklsa --workbench C:\workspace\projects\SST-Workbench doctor
python -m sst_pklsa --workbench C:\workspace\projects\SST-Workbench resolve --output resolved.json
python -m sst_pklsa --workbench C:\workspace\projects\SST-Workbench inventory --output inventory.json.gz
python -m sst_pklsa --workbench C:\workspace\projects\SST-Workbench carriers --topology 3_1 --output carriers_3_1.json
python -m sst_pklsa --workbench C:\workspace\projects\SST-Workbench qualify --topology 3_1 --config configs\qualification_basic.json --output qualification\3_1
```

For a byte-level source snapshot:

```bat
python -m sst_pklsa --workbench C:\workspace\projects\SST-Workbench inventory --deep-hash --output inventory_deep.json.gz
```

## Source resolution order

1. live `10_docs/registry/catalog_index.json` and `family_hierarchy.json`;
2. canonical paths declared in `configs/source_contract_v1.json`;
3. catalog-family paths for producer/library/tool dependencies;
4. explicit legacy aliases only when canonical paths are absent;
5. heuristic repository scan only as **audit output**, never as automatic scientific admission.

The bundled registry snapshot is fallback metadata for portability. A live Workbench registry always wins.

## Scientific guards

- `Quarantine/` is negative/audit evidence only.
- generated QHP/PTSA/conditioning output is not counted as upstream source evidence;
- byte-identical mirrors share an independence group;
- KnotAtlas/KAtlas reference data is not called native metric 3-D geometry;
- topology naming crosswalks are recorded only when present in upstream reference data;
- missing or undecodable geometry fails closed;
- per-observable geometry convergence remains independent.

## High-resolution observables

The qualification core calculates a resolution ladder for:

`L`, `kappa_max`, `kappa_rms`, `sigma_kappa`, `tau_rms`, `Wr`, `ACN`, `d_min`, `dcsd`, `reach`, `Thi`, `Rop`, and `ropelength_reach`.

`Thi = 2*reach` is emitted explicitly as the diameter convention used for direct comparison with historical Gilbert/KnotPlot `L/D` values. `reach` is retained separately.

## Output convention

Scripts write to:

```text
./SST_Parametric_Knot_Link_Seed_Atlas_v0.3.0-outputs/
```

and `run_90_pack.cmd` creates:

```text
../SST_Parametric_Knot_Link_Seed_Atlas_v0.3.0-outputs.zip
```

## Release boundary

The package can be validated without the full Workbench via synthetic tests and bundled registry snapshots. That is not equivalent to a full publication qualification over the real local data tree. Run `run_all_publication.cmd` on the local Workbench before treating source coverage and high-resolution metrics as final evidence.

## Packaged release note (2026-09-10)

This distributable includes the repository-native `sst_pklsa` resolver/facade and the complete tested `pklsa_builder` qualification core from builder v0.2.0. The resolver uses the live Workbench canonical paths first; bundled registry snapshots are provenance/fallback metadata. The qualification core retains compatibility with the PKLSA v0.2.0 atlas as a base input. A full multi-source publication claim requires executing the included publication pipeline on the actual Workbench; this ZIP does not embed or duplicate the multi-GB raw knot datasets.
