# SST_Two_Harmonic_Phase_Chirality_Floquet_Blind_Falsifier v0.2.0

Numerics: **FAIL**
Physics: **UNTESTED**
Backend: `native`

## Gates
- G0_source_leakage: FAIL — {'pass': False, 'n_hits': 8}
- G1_frozen_input_hashes: PASS — {'pass': True, 'n': 4}
- G2_one_drive_class_exact_C3: PASS — {'blind_value_min': 7.892825783876711e-15, 'threshold': 1e-10, 'pass': True}
- G3_finite_core_equivariance_low_branch: PASS — {'value': 4.519201772951241e-16, 'threshold': 2e-05, 'pass': True}
- G4_blind_control_separation: PASS — {'value': 13374394425069.572, 'threshold_min': 20.0, 'pass': True}
- G5_temporal_refinement: PASS — {'value': 2.1458147284068611e-10, 'threshold': 0.003, 'pass': True}
- G6_length_drift: PASS — {'value': 0.0022143511953128616, 'threshold': 0.1, 'pass': True}
- G7_mesh_quality: PASS — {'value': 0.11264315917817828, 'threshold': 0.2, 'pass': True}

## Floquet gate
SKIP_NO_CERTIFIED_RPO

No Floquet multipliers are emitted in this release. A certified periodic or relative-periodic orbit is an upstream prerequisite.
