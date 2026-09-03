# Input formats

## Geometry campaign
`run_all*.cmd` recursively scans the dataset for `.txt`, `.xyz`, `.dat`, and `.csv` files containing XYZ triples. Blank lines or `component`/`>` markers separate closed components.

Default dataset:

```text
..\..\KnotPlot\knots\final
```

The loader fails closed when no usable closed component is parsed.

## External field-matter closure CSV
Columns are optional by gate; missing a required pair closes that gate rather than fabricating it.

```text
scale_a,omega_rad_s,M_E_kg,M_I_kg,C_p,beta_knot,beta_fluid,energy_drift_rel
```

## Topology
A filename such as `knot_6.3` is only a hypothesis label in v0.2.0. The package does not claim independent topology certification. If you need topology-certified physical PASS status, feed geometries that have already passed the SST Knot Library trust chain and preserve their geometry SHA-256 in your campaign record.
