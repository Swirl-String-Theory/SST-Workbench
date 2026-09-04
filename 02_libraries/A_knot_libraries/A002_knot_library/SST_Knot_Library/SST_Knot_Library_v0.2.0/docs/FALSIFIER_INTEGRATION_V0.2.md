# Integration with latest SST falsifiers

Use `prepare_for_falsifier()` as the single ingress point for centerline geometry.

Recommended campaign metadata fields:

```json
{
  "expected_topology": "6_2",
  "topology_certification": {"status": "CERTIFIED|UNVERIFIED|..."},
  "katlas_snapshot_id": "...",
  "katlas_snapshot_sha256": "...",
  "source_family": "ideal_txt|knotplot_fseries|ridgerunner|katlas_braid|analytic|...",
  "source_sha256": "...",
  "geometry_sha256": "...",
  "qualification": {},
  "convergence": []
}
```

## Same-topology, independent-embedding gate

For a knot K, compare several pre-dynamics families without changing the physics solver:

```text
KnotPlot relaxed
Ridgerunner
ideal.txt
fseries XYZ
KAtlas braid closure
analytic/S3/Lissajous control when available
```

A physically meaningful attractor should not be an artifact of one historical seed representation.

## Blindness

Topology/geometry qualification is performed before outcome analysis. Candidate labels are replaced by blind IDs; private reveal maps IDs back to source family and parameters. Do not discard candidates after seeing Euler/Floquet outcomes except by preregistered gates.
