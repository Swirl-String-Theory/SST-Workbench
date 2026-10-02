# SP10 reproducibility gate

Generated: 2026-09-05T08:30:16Z

## Summary

| status | count |
|--------|------:|
| pass | 28 |
| structural | 59 |
| skipped | 0 |
| fail | 0 |
| **total** | **87** |

Tier 1/2 passes: **24** (need ≥10 for done-criteria).

## Dataset integrity

- moves checked: 13
- files hashed: 544
- missing: 0
- mismatched (move corruption): 0
- freeze drift (post-SP00 content change, move OK): 20
- ok: True

## Per-family rows

| catalog_id | version | tier | native_build | basic_run | extended_run | equivalence | tolerance | status | note |
|------------|---------|------|--------------|-----------|--------------|-------------|-----------|--------|------|
| A001 | v0_8_19 | structural | n/a | n/a | n/a | n/a | - | structural | no tier1 zip and no pytest smoke; latest present; project.json OK |
| A002 | v0_8_19 | 1 | n/a | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (sst_nonfit_prediction_harness_v0_8_19_outputs.zip, 14 members) |
| A003 | - | structural | n/a | n/a | n/a | n/a | - | structural | unversioned / no runnable latest |
| A004 | v0.4.0 | 1 | n/a | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (SST_dimensionless_dynamic_predictions_v0.4.0_iso_gamma_area_dynamic_clock_outputs.zip, 38 members); on-disk overlap agree=1 disagree=4 |
| A006 | v0.2.0 | 1 | n/a | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (SST_contact_billiard_hydrodynamic_falsifier_v0.2.0_outputs.zip, 589 members); on-disk overlap agree=5 disagree=0 (matches on-disk outputs) |
| A007 | v0.4.0-alpha.1 | structural | present | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| A008 | v0.1.3 | structural | present | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| A009 | v0.1.1 | structural | present | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| A010 | v0.5.0 | 3 | present | pass | n/a | self-test | pytest | pass | pytest smoke OK; latest present; project.json OK |
| A011 | v0.3.1 | 1 | present | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (1_Maxwell_SST_Kinetic_Falsifier_v0.3.1_outputs.zip, 198 members); on-disk overlap agree=4 disagree=1 |
| A012 | v0.2.0 | structural | present | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| A013 | v0.2.0 | structural | present | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| A014 | v0.2.0 | structural | present | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| A015 | v0.2.0 | structural | present | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| A016 | v0.1.1 | structural | present | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| A017 | v0.1.1 | 1 | present | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (Einstein_SST_Emergent_Metric_Poisson_Closure_Gates_v0.1.1_outputs.zip, 128 members); on-disk overlap agree=3 disagree=2 |
| A018 | v0.1.0 | structural | present | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| A019 | v0.1.1 | structural | present | n/a | n/a | n/a | - | structural | no tier1 zip and no pytest smoke; latest present; project.json OK |
| A020 | v0.1.0 | 1 | present | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (SST_6Source_Blind_Falsifier_v0.1.0_outputs.zip, 770 members); on-disk overlap agree=3 disagree=2 |
| A021 | v0.3.0 | structural | present | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| A022 | v0.1.1 | 1 | present | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (SST_Fourier_vs_Ideal_Blind_Falsifier_v0.1.1_outputs.zip, 72 members); on-disk overlap agree=2 disagree=3 |
| A023 | v0.4.8 | structural | present | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| A024 | v0.3.0 | 1 | present | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (SST_Threaded_Hole_Substrate_Blind_Falsifier_v0.3.0_outputs.zip, 3777 members); on-disk overlap agree=0 disagree=5 (local outputs differ from archive; archive remains the baseline) |
| A025 | v0.3.0 | structural | present | n/a | n/a | n/a | - | structural | no tier1 zip and no pytest smoke; latest present; project.json OK |
| A026 | v0.2.0 | structural | present | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| A027 | v0.2.1 | 1 | present | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (SST_vArrow_Spectral_Blind_Falsifier_v0.2.1_outputs.zip, 9 members) |
| A028 | v0.1.2 | structural | present | n/a | n/a | n/a | - | structural | no tier1 zip and no pytest smoke; latest present; project.json OK |
| A029 | v0.1.2 | 1 | present | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (SST_Finite_Core_Axial_Toroidal_Phase_Delay_Blind_Falsifier_v0.1.2_outputs.zip, 2666 members); on-disk overlap agree=0 disagree=5 (local outputs differ from archive; archive remains the baseline) |
| A030 | v0.1.1 | 1 | n/a | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (SST_Material_Phase_EFT_Falsifier_v0.1.1_outputs.zip, 14 members); on-disk overlap agree=2 disagree=2 |
| A031 | v0.1.0 | 1 | n/a | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (SST_Adaptive_Period_Aware_RPO_Multiple_Shooting_Floquet_Blind_Falsifier_v0.1.0_outputs.zip, 187 members); on-disk overlap agree=5 disagree=0 (matches on-disk outputs) |
| A032 | v0.1.0 | 3 | present | pass | n/a | self-test | pytest | pass | pytest smoke OK; latest present; project.json OK |
| A033 | v0.1.0 | 1 | present | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (SST_Breathing_Stretching_Return_Phase_Causality_Blind_Falsifier_v0.1.0_outputs.zip, 794 members); on-disk overlap agree=4 disagree=1 |
| A034 | v0.1.3 | 1 | present | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (SST_QHP_Stability_Landscape_Blind_Falsifier_v0.1.3_outputs.zip, 72 members); on-disk overlap agree=5 disagree=0 (matches on-disk outputs) |
| A035 | v0.2.2 | 1 | present | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (SST_Intrinsic_Modal_Swirl_Clock_Blind_Falsifier_v0.2.2_outputs.zip, 44 members); on-disk overlap agree=5 disagree=0 (matches on-disk outputs) |
| A036 | v0.1.1 | structural | present | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| A037 | v0.2.0 | 1 | n/a | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (SST_Chirality_Helicity_Transport_Polarity_Falsifier_v0.2.0_outputs.zip, 116 members); on-disk overlap agree=4 disagree=1 |
| A038 | v0.3.3 | structural | present | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| A039 | v0.1.1 | structural | present | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| A040 | v0.1.0 | structural | present | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| A041 | v0.4.1 | structural | present | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| A042 | v0.2.0 | structural | present | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| B001 | - | structural | n/a | n/a | n/a | n/a | - | structural | unversioned / no runnable latest |
| B002 | v3 | structural | n/a | n/a | n/a | n/a | - | structural | no tier1 zip and no pytest smoke; latest present; project.json OK |
| B003 | - | structural | n/a | n/a | n/a | n/a | - | structural | unversioned / no runnable latest |
| B004 | v19 | structural | n/a | n/a | n/a | n/a | - | structural | no tier1 zip and no pytest smoke; latest present; project.json OK |
| B005 | v0_6 | structural | n/a | n/a | n/a | n/a | - | structural | no tier1 zip and no pytest smoke; latest present; project.json OK |
| C001 | v16B0 | structural | n/a | n/a | n/a | n/a | - | structural | no tier1 zip and no pytest smoke; latest present; project.json OK |
| C002 | v2 | structural | n/a | n/a | n/a | n/a | - | structural | no tier1 zip and no pytest smoke; latest present; project.json OK |
| C003 | v7 | structural | n/a | n/a | n/a | n/a | - | structural | no tier1 zip and no pytest smoke; latest present; project.json OK |
| C004 | v0.8.19 | structural | n/a | n/a | n/a | n/a | - | structural | no tier1 zip and no pytest smoke; latest present; project.json OK |
| C005 | v0.6.1 | structural | present | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| C006 | v0.1.1 | 3 | present | pass | n/a | self-test | pytest | pass | pytest smoke OK; latest present; project.json OK |
| C007 | - | structural | n/a | n/a | n/a | n/a | - | structural | unversioned / no runnable latest |
| D001 | - | structural | n/a | n/a | n/a | n/a | - | structural | unversioned / no runnable latest |
| D002 | v18 | structural | n/a | n/a | n/a | n/a | - | structural | no tier1 zip and no pytest smoke; latest present; project.json OK |
| D003 | - | structural | n/a | n/a | n/a | n/a | - | structural | unversioned / no runnable latest |
| D004 | v0_2 | structural | n/a | n/a | n/a | n/a | - | structural | no tier1 zip and no pytest smoke; latest present; project.json OK |
| D005 | v0.1.4 | structural | present | n/a | n/a | n/a | - | structural | no tier1 zip and no pytest smoke; latest present; project.json OK |
| D006 | v0.3.0 | structural | n/a | n/a | n/a | n/a | - | structural | no tier1 zip and no pytest smoke; latest present; project.json OK |
| D007 | v0.1.0 | 1 | n/a | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (Sutcliffe_HSS_feasibility_gate_v0.1.0_outputs.zip, 9 members); on-disk overlap agree=4 disagree=0 (matches on-disk outputs) |
| D008 | v0.2.0 | 1 | n/a | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (KnotPlot_3p1_MissingParameter_Command_Certification_v0.2.0_outputs.zip, 200 members) |
| D009 | v0.3.2 | 1 | n/a | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (KnotPlot_3p1_Comprehensive_Dynamics_Parameter_Atlas_v0.3.2_outputs.zip, 2847 members) |
| E001 | v0.2.0 | 1 | present | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (SST21D_knot_order_pipeline_v0.2.0_outputs.zip, 480 members); on-disk overlap agree=3 disagree=2 |
| E002 | v0.1.7 | 1 | n/a | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v0.1.7_outputs.zip, 423 members) |
| E003 | v0.1.3 | 1 | n/a | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (KnotPlot_3p1_Trefoil_Seed_Campaign_v0.1.3_outputs.zip, 435 members) |
| E004 | v0.2.4 | 1 | n/a | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (Trefoil_Balance_Point_Campaign_v0.2.4_outputs.zip, 1362 members) |
| E005 | v0.1.0 | structural | n/a | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| E006 | v0.3.2 | 1 | n/a | baseline-zip | n/a | pass | exact/scientific | pass | tier1 baseline zip present (KnotPlot_MultiTopology_QHP_Sweep_v0.3.2_outputs.zip, 5100 members) |
| E007 | v0.1.0 | structural | n/a | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| E008 | v2.0.0 | structural | n/a | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| E009 | v1.0.0 | structural | n/a | n/a | n/a | n/a | - | structural | no tier1 zip and no pytest smoke; latest present; project.json OK |
| F001 | v10 | structural | n/a | n/a | n/a | n/a | - | structural | no tier1 zip and no pytest smoke; latest present; project.json OK |
| F002 | v0_8_19 | structural | n/a | n/a | n/a | n/a | - | structural | no tier1 zip and no pytest smoke; latest present; project.json OK |
| F003 | v2 | structural | n/a | n/a | n/a | n/a | - | structural | no tier1 zip and no pytest smoke; latest present; project.json OK |
| F004 | v3b | structural | n/a | n/a | n/a | n/a | - | structural | no tier1 zip and no pytest smoke; latest present; project.json OK |
| A001 | v0.1.3 | 3 | present | pass | n/a | self-test | pytest | pass | pytest smoke OK; latest present; project.json OK |
| A002 | - | structural | n/a | n/a | n/a | n/a | - | structural | unversioned / no runnable latest |
| B001 | v0.1.2 | structural | n/a | n/a | n/a | n/a | - | structural | 02_libraries pack without research entry point |
| A001 | - | structural | n/a | n/a | n/a | n/a | - | structural | unversioned / no runnable latest |
| A002 | - | structural | n/a | n/a | n/a | n/a | - | structural | unversioned / no runnable latest |
| B001 | v0.2.2 | structural | n/a | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |
| C001 | - | structural | n/a | n/a | n/a | n/a | - | structural | unversioned / no runnable latest |
| D001 | - | structural | n/a | n/a | n/a | n/a | - | structural | unversioned / no runnable latest |
| A001 | - | structural | n/a | n/a | n/a | n/a | - | structural | unversioned / no runnable latest |
| A002 | - | structural | n/a | n/a | n/a | n/a | - | structural | unversioned / no runnable latest |
| A003 | v7.6.25b-m1 | structural | n/a | n/a | n/a | n/a | - | structural | 05_apps pack without research entry point |
| A004 | v0.2.0 | structural | n/a | n/a | n/a | n/a | - | structural | tests/ present but no test_smoke*; latest present; project.json OK |

## Notes

Tier 1 uses archived `*_outputs.zip` baselines (and on-disk output overlap when present). Tier 3 is a pytest smoke from the new path. `structural` means the latest pack is intact but was not re-run in this gate.

Freeze drift: some Fremlin / Ideal_Sources / Knot_Library files no longer match `checksums.sha256` from SP00, but the legacy junction and the new catalog path are byte-identical — the move did not corrupt them; content changed after the freeze.
