# Optional externally sourced 3-D knot geometries

External carrier manifest schema: `sst.a003.external-carriers/1`. Exactly 3
numeric columns per `.xyz`, SHA-256 verified, path relative to the canonical
Workbench root, and declared `seed` in F3/F4 topology. Provide at least two
truly separate *computational* provenance source groups (for example a genuine
KnotPlot/Ridgerunner relaxed geometric export and a geometrically independently
constructed Gilbert ideal knot). Do not pretend a decimated/copy/mirror file is
another provider. `source_role` must be `computed_geometry_not_empirical`.

Example structure (SHA and paths MUST be supplied from measured local originals):

```json
{
  "schema": "sst.a003.external-carriers/1",
  "carriers": [
    {
      "name": "checked-source-description",
      "workbench_rel_path": "03_data/A_knots/<ACTUAL_DIRECTORY>/<ACTUAL_XYZ>.xyz",
      "sha256": "<64 lowercase hex digest of the actual file>",
      "seed": "fibonacci_torus_F3",
      "provider_group": "<real original producer>",
      "independence_group": "<real original lineage>",
      "source_role": "computed_geometry_not_empirical"
    }
  ]
}
```

No fake source is admitted. If paths, SHA, topology evidence, or source
independence are missing, G6P16 remains UNRESOLVED or reports integrity FAIL.
This optional path uses the C005 field in its own source coordinates and
reports no physical calibration or independent Euler model.
