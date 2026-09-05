# Reproducibility Policy — v0.4.0

Every release is intended to be sufficient to reconstruct the conclusions of all earlier releases without relying on a later code checkout.

## Historical immutable ZIPs

`release_history/` contains exact ZIP artifacts for:

- `SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v0.1.0.zip`
- `SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v0.1.1.zip`
- `SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v0.2.0.zip`
- `SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v0.3.0.zip`

`release_history/INDEX.sha256` verifies them byte-for-byte.

## Input preservation

Two layers are retained:

1. the exact canonical selected files in `repro_inputs/panel/`;
2. the complete source archives in `repro_inputs/source_archives/`.

The older v0.1--v0.3 trefoil inputs remain at `repro_inputs/knot.3_1.fseries` and `repro_inputs/knot_3.1_final.txt` for compatibility with their historical reproduction scripts.

## Recompute historical releases

```bat
run_reproduce_history_basic.cmd
run_reproduce_history_extended.cmd
```

The historical runner extracts each old ZIP and executes that version's own code against its preserved trefoil inputs. The current v0.4 panel is then executed separately with its own generic multi-topology preregistration. Results are kept distinct because the perturbation bases are not identical.

## Recompute the v0.4 canonical panel

```bat
run_panel_basic.cmd
run_panel_extended.cmd
```

## Survey all bundled geometries

```bat
run_archive_survey.cmd
```

The survey intentionally uses a lighter config and must not be substituted for BASIC/EXTENDED confirmation.

## Reference snapshots

`reference_results/` contains convenience snapshots from validated runs. They are never read by the scoring code. Deleting them does not change a recomputation.

## Resume semantics

An interrupted v0.4 panel may resume from existing blind per-dataset analysis files. Resume is refused if the existing preregistered JSON config differs from the requested config. Thus completion cannot silently mix thresholds or resolutions.

## v0.4.1 complete-archive campaigns

`run_archive_campaign.py` enumerates all 78 bundled Fremlin `.fseries` files and all 49 bundled KnotPlot/RidgeRunner `*_final.txt` files. The enumeration is recorded in `ARCHIVE_INVENTORY.csv` with SHA-256 values. `run_archive_validate.cmd` must report 127/127 before a release-scale campaign.

The exact prior v0.4.0 release is embedded in `release_history/` and hashed in `release_history/INDEX.sha256`. Thus v0.4.1 contains both the exact previous executable source tree and all source geometry archives required to recalculate its conclusions.

For large FULL runs, deterministic sharding is permitted as a workload mechanism. Shards must all use the immutable `configs/archive_full.json`; merged summaries do not alter per-shard preregistered gates.
