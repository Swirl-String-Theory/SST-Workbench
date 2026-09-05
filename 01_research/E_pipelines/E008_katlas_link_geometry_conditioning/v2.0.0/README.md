# SST Katlas Link Geometry Conditioning v2.0.0

A geometry-only compiler for Katlas link PD presentations. It deliberately does **not** inspect Biot–Savart lifetime, modal-clock outcomes, or any later dynamical score.

Pipeline:

`Katlas PD -> raw crossing-correct 3D scaffold -> uniform arclength -> minimum harmonic truncation -> optional H=1 circularization -> numerical homotopy-clearance guard -> linking-matrix guard -> conditioned seed`

The output remains generated geometry:
- `source_coordinates=false`
- `geometry_origin=generated_from_katlas_pd_conditioned`
- `raw_translator=SST-KATLAS-PD-3D-1.0`
- `conditioner=SST-KATLAS-ISOTOPY-HARMONIC-2.0`

## Quick Hopf test

```bat
run_focus_L2a1.cmd C:\workspace\projects\SST-Workbench\Katlas_Sources_v0.2.2_Outputs
```

## Full link library

```bat
run_all.cmd C:\workspace\projects\SST-Workbench\Katlas_Sources_v0.2.2_Outputs outputs\Katlas_Conditioned_v2
```

Each conditioned record contains `katlas.json`, `conditioned_geometry.npz`, `conditioning.json`, and per-component XYZ files.

The topology guard is numerical: it checks a sampled straight-line homotopy for positive clearance and requires the integer-rounded pairwise Gauss-linking matrix to remain unchanged. This is stronger than checking linking number alone but is not a formal computer-assisted isotopy proof.

## Determinism and safe fallback

The planar scaffold uses canonical integer graph node ids so Python hash randomization cannot change the metric embedding between processes. If no harmonic candidate satisfies all frozen topology/clearance/curvature gates, the compiler emits `FALLBACK_RAW_UNIFORM` rather than forcing a conditioned shape.
