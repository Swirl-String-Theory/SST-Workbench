# Source coverage contract for v0.3.0

The v0.3.0 builder is intentionally coverage-auditable. For each topology, `source_matrix.csv` always contains rows for:

```text
knotplot_relaxed
knotplot_ideal
fremlin_fourier
gilbert_ideal
katlas_braid_derived
ridgerunner
ptsa
siaf
knotinfo_3d
```

A zero is evidence of a gap, not a reason to synthesize a replacement. KAtlas topology reference availability is reported separately from KAtlas-braid-derived 3-D controls.

The design is open-ended: new upstream families can be added without changing the topology directory schema.
