# TRPL_INPUT_V1 producer contract

Physical evaluation uses a JSON manifest plus an NPZ array file.

Required manifest fields:

```json
{
  "schema": "TRPL_INPUT_V1",
  "arrays_file": "data.npz",
  "producer": {
    "id": "anonymous-or-stable-id",
    "version": "...",
    "dynamics_kind": "full_field_euler|finite_core_filament|other",
    "time_reversal_map": "conjugation|producer_defined",
    "reversibility_certified": true,
    "reversibility_residual": 0.0
  },
  "conditions": {
    "external_forcing": false,
    "time_odd_bias": false,
    "material_phase_observable": true,
    "phase_derived_from_centerline_only": false,
    "spatial_converged": true,
    "temporal_converged": true,
    "core_converged": true
  },
  "runs": [
    {
      "run_id": "R001",
      "pair_id": "P001",
      "pair_role": "A",
      "geometry_group": "G01",
      "source_group": "S01",
      "neutral_selection": true
    }
  ]
}
```

Required NPZ arrays:

- `t`: `(nt,)`, real and strictly increasing.
- `eta`: `(nruns, nt, 2)`, complex modal amplitudes.
- `energy`: `(nruns, nt)`, producer energy diagnostic in any internally consistent unit.

Optional:

- `residual`: `(nruns, nt)` producer stationarity/residual diagnostic.

The evaluator does **not** infer a material phase from centerline geometry. If the phase observable is only a geometric surrogate, the physical gate is `INDETERMINATE`.

For a producer-defined time-reversal map, the producer must additionally supply and certify its representation. v0.1.0 evaluates the default conjugation representation and records non-default maps as `INDETERMINATE_NOT_IMPLEMENTED` rather than guessing.
