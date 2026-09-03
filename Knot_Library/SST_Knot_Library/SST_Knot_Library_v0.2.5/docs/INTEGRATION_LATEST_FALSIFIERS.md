# Integration into the latest SST falsifiers

This file is retained as the short operational checklist. See `FALSIFIER_INTEGRATION_V0.2.md` for the full topology-aware schema.

## 1. Trefoil Dynamic Seed Qualification Mega Falsifier

Use blind parameterized geometry families (`R`, radial bulge `a`, axial weave `b`) plus independent representations. Geometry and topology gates precede dynamics; parameters must not be selected after seeing dynamic outcomes.

## 2. Self-Confinement / Restoring-Force Balance

Export one immutable arclength-uniform centerline per accepted candidate. Perturbations happen after qualification. The restoring force remains entirely in the downstream Euler/finite-core solver.

## 3. Threaded-hole falsifier

Use the same expected topology with independent embeddings:

- original KnotPlot/Ridgerunner/ideal/fseries seed;
- Fourier-smoothed seed;
- shape-neighbor seeds;
- S3 stereographic null controls, tagged nonphysical;
- KAtlas-braid topology-control seeds;
- Bishop-frame material bundles.

A visually persistent hole is not by itself a topological invariant.

## 4. Finite-core/eigenmode/phase-delay tests

The knot library supplies geometry, topology status, frames and provenance only. Any phase/group delay is measured from dynamics, never inserted as a free geometry feedback parameter.

## 5. Required provenance

```json
{
  "knot_library": "sst-knot-library/0.2.5",
  "expected_topology": "3_1",
  "topology_certification": {"status": "CERTIFIED|UNVERIFIED|..."},
  "katlas_snapshot_id": "katlas-core-sst-2026-08-30",
  "katlas_snapshot_sha256": "...",
  "source_family": "ideal_txt|knotplot_fseries|ridgerunner|katlas_braid|analytic",
  "source_sha256": "...",
  "geometry_sha256": "...",
  "resample_N": 512,
  "qualification": {},
  "convergence": [],
  "blind_candidate_id": "C0001"
}
```
