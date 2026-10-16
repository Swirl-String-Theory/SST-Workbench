# SST_Two_Harmonic_Phase_Chirality_Floquet_Blind_Falsifier v0.2.2

Numerics: **PASS**
Physics: **UNTESTED**
Backend: `native`

## Gates
- G0_source_leakage: PASS — {'pass': True, 'n_hits': 0, 'n_scanned': 18, 'n_read_errors': 0}
- G1_frozen_input_hashes: PASS — {'pass': True, 'n': 4}
- G2_one_drive_class_exact_C3: PASS — {'blind_value_min': 7.892825783876711e-15, 'threshold': 1e-10, 'pass': True}
- G3_finite_core_equivariance_low_branch: PASS — {'value': 2.032107613259019e-15, 'threshold': 2e-05, 'pass': True}
- G4_blind_control_separation: PASS — {'value': 5372028582725.384, 'threshold_min': 20.0, 'pass': True}
- G5_temporal_refinement: PASS — {'value': 4.672024318879767e-10, 'threshold': 0.0015, 'pass': True}
- G6_length_drift: PASS — {'value': 0.03848787404048227, 'threshold': 0.12, 'pass': True}
- G7_mesh_quality: PASS — {'value': 0.19764157951458258, 'threshold': 0.22, 'pass': True}

## Floquet gate
SKIP_NO_CERTIFIED_RPO

No Floquet multipliers are emitted in this release. A certified periodic or relative-periodic orbit is an upstream prerequisite.
