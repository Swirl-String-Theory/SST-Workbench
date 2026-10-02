# SST SC-III Koopman/DMD Complex Phase-Clock Blind Falsifier v0.1.0

SC-III is a new falsifier. It does **not** modify the SC-I, SC-II, or SC-IIb definitions after their outcomes.

## Hypothesis

A vortex geometry may possess a reproducible internal complex phase even when neither the full shape nor a frozen scalar/POD pair recurs. SC-III therefore tests a discovery-learned complex DMD/Koopman coordinate whose local eigenspace may drift slowly in holdout.

Discovery learns a frozen POD observable basis and a complex DMD eigenmode. Holdout is split into pre-defined overlapping windows. Each local complex mode must be matched to the previous one by mode overlap and frequency continuity; its arbitrary complex gauge is removed by parallel transport. The stitched complex coordinate is then tested as a clock.

Primary channel: **natural only**. The odd/probe channel remains diagnostic/null only.

## First run: reuse the existing 333 Stage-A trajectories

```bat
run_sciii_from_stage_a.cmd C:\workspace\projects\SST-Workbench\SST_Intrinsic_Modal_Swirl_Clock\SST_Intrinsic_Modal_Swirl_Clock_Blind_Falsifier_v0.2.2.5\outputs\basic
```

No Stage-A Biot–Savart evolution is recomputed unless SC-III produces provisional candidates that require low/high mesh-gauge replay.

## New campaign

```bat
run_all.cmd --libraries=Fremlin,Gilbert,Katlas --min-carriers=2 --kind=knots
```

or links:

```bat
run_all.cmd --libraries=Gilbert,Katlas --min-carriers=2 --kind=links
```

## Conditioned Katlas links

`src/sst_modal_clock/sources.py` recognizes `conditioned_geometry.npz` next to a Katlas `katlas.json`. Therefore the output tree of **SST Katlas Link Geometry Conditioning v2.0.0** can be used directly as the Katlas source root in config. Generated geometry remains explicitly marked `source_coordinates=false`.

## Scientific separation

SC-III existence and Stage-B mechanism claims remain separate. A mesh/provenance-certified Koopman phase clock may PASS while the stretch→phase-rate mechanism FAILS or remains INDETERMINATE.
