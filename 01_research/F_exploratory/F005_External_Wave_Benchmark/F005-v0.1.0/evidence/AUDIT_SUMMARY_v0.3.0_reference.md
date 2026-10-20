# F005 external data audit v0.3.0 — DEVELOPMENT

**P5: REVIEW_NO_BLIND_CERTIFICATION**; **P6: ARX_DEV_ONLY_NOT_EULER**; P7 NOT RUN; P8 UNRESOLVED.

## Source integrity

Split: {'status': 'PASS', 'count': 9822, 'counts': {'STANDARD_TEST': 750, 'STANDARD_TRAIN': 3500, 'STANDARD_VALIDATION': 750, 'OPTIMIZED_OOD': 4822}, 'missing_count': 0, 'extra_count': 0, 'duplicate_ids': [], 'issues': []}

Metadata group collisions: []

Input exact-duplicate cross-partition groups: 0

Input approximate shape cross-partition groups (diagnostic only): 529

## Model

{
  "status": "ARX_DEV_ONLY_NOT_EULER",
  "training": {
    "num_rows": 3500,
    "num_pairs": 5243000,
    "regularization": 2.415263123927513e-05,
    "fit_parameterization": "second difference (numerical conditioning)",
    "features": "elevation(t), elevation(t)-elevation(t-dt), acceleration(t)*dt^2",
    "target": "elevation(t+dt)-2*elevation(t)+elevation(t-dt) [m]"
  },
  "model": {
    "discrete_A": 1.9856661039519918,
    "discrete_B": -0.9908696423084401,
    "acceleration_coefficient_C": -1.118156917616826,
    "pole_real_imag": [
      [
        0.9928330519759958,
        0.07177864036375547
      ],
      [
        0.9928330519759958,
        -0.07177864036375547
      ]
    ],
    "poles_stable": true,
    "complex_oscillatory_poles": true,
    "ringdown_gamma_per_s": 1.1465368587688405,
    "ringdown_frequency_hz": 2.871601616596693,
    "central_difference_coupling_K_dimensionless": 1.123284914144663
  },
  "validation": {
    "validation_rows": 750,
    "samples": 1123500,
    "one_step_rmse_m": 1.5650351975287902e-05,
    "persistence_rmse_m": 0.0002037203568403973,
    "improvement_over_persistence_percent": 92.31772797867764,
    "warning": "Teacher-forced one-step error; NOT a multi-second open-loop wave prediction"
  },
  "no_test_peeking": true,
  "limitations": [
    "one-step teacher-forced",
    "candidate split is non-blind",
    "not nonlinear Euler",
    "not PKLSA",
    "no field velocity measured"
  ]
}

**Do not claim physical SST/PKLSA validation, certified blind split, or Euler closure.**
