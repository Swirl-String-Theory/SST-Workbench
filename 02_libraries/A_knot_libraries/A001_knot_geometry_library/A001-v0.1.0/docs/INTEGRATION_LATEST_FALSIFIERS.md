# Integration into the latest SST falsifiers

## 1. Trefoil Dynamic Seed Qualification Mega Falsifier

Replace ad-hoc seed creation with a blind parameterized family. Candidate identity is hidden before dynamics. Primary coordinates:

- `R` major radius
- `a` radial bulge
- `b` axial weave
- optional Fourier smoothing level for imported centerlines
- optional Bishop-frame material bundle parameters for a separate thread-structure arm

Do **not** select parameters from dynamic outcome. Geometry qualification precedes blind sealing.

## 2. Self-Confinement / Restoring-Force Balance

For every accepted geometry, export one immutable arclength-uniform centerline. Perturbations should be generated after qualification. `perturb_normal_modes()` can provide signed geometric perturbations, but the force response remains entirely in the downstream Euler/finite-core solver.

## 3. Threaded-hole falsifier

Use the same centerline with several embedding controls:

- original seed,
- Fourier-smoothed seed,
- shape-neighbor seeds in `(a,b)`,
- S3 stereographic null controls (tagged nonphysical),
- Bishop-frame bundles.

If the apparent hole changes under topology-preserving S3 controls while true material-thread/linking observables do not, classify the hole metric as embedding-sensitive rather than topological.

## 4. Finite-core / eigenmode / phase-delay tests

This library supplies geometry and frames only. Any phase/group delay must be **measured from the simulation**, never inserted as a free geometry or feedback parameter.

## 5. Required provenance fields

Recommended per candidate:

```json
{
  "geometry_library": "sst-knot-geometry/0.1.0",
  "constructor": "track_trefoil",
  "constructor_parameters": {},
  "resample_N": 512,
  "geometry_sha256": "...",
  "blind_candidate_id": "C0001",
  "geometry_gates": {},
  "control_class": "physical_seed | nonphysical_s3_control"
}
```
