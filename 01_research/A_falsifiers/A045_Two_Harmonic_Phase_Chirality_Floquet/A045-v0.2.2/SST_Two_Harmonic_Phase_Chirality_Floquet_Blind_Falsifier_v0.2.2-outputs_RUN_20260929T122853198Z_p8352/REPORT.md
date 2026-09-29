# SST_Two_Harmonic_Phase_Chirality_Floquet_Blind_Falsifier v0.2.2

Numerics: **PASS**
Physics: **UNTESTED**
Backend: `python`

## Gates
- G0_source_leakage: PASS — {'pass': True, 'n_hits': 0, 'n_scanned': 18, 'n_read_errors': 0}
- G1_frozen_input_hashes: PASS — {'pass': True, 'n': 4}
- G2_one_drive_class_exact_C3: PASS — {'blind_value_min': 7.892825783876711e-15, 'threshold': 1e-10, 'pass': True}
- G3_finite_core_equivariance_low_branch: PASS — {'value': 1.571662816313547e-16, 'threshold': 1e-06, 'pass': True}
- G4_blind_control_separation: PASS — {'value': 10727108635288.107, 'threshold_min': 20.0, 'pass': True}
- G5_temporal_refinement: PASS — {'value': 5.447720730941643e-09, 'threshold': 0.01, 'pass': True}
- G6_length_drift: PASS — {'value': 0.0005236472461496978, 'threshold': 0.05, 'pass': True}
- G7_mesh_quality: PASS — {'value': 0.03844663811852288, 'threshold': 0.12, 'pass': True}

## Floquet gate
SKIP_NO_CERTIFIED_RPO

No Floquet multipliers are emitted in this release. A certified periodic or relative-periodic orbit is an upstream prerequisite.
