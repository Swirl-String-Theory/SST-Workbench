# Changelog

## v0.1.1
- Maintenance/reporting-only release.
- Adds `sync-sc2-reporting`: corrects stale SC-II final summary precedence without recomputing trajectories, modal metrics, gates, or candidates.
- `run_sciib_from_stage_a.cmd` invokes the sync only when an existing SC-II Stage-A summary is present.
- SC-IIb scientific gates and native physics are unchanged from v0.1.0.


## v0.1.0 — SC-IIb Frozen Modal-Pair / Subspace Phase Clock

- New falsifier; SC-II scalar-phase gates are not modified.
- Discovery-frozen POD mode-pair selection with energy, near-degeneracy,
  quadrature and directed modal-angular-momentum gates.
- Holdout phase is `atan2(a_j,a_i)` with no holdout detrending.
- Added phase wraps, directionality, period/omega coherence, phase diffusion,
  radius persistence and out-of-sample prediction gates.
- Added explicit orthogonal basis-gauge audit inside the frozen 2-D subspace.
- Natural channel is the only primary channel; odd/probe remains diagnostic.
- Added low/high mesh-gauge certification using the exact frozen pair.
- Added source-family-balanced provenance analysis.
- Added Stage-B phase-tangent stretch -> phase-velocity mechanism test with
  material vs fixed-core specificity.
- Added `run_sciib_from_stage_a.cmd` to reuse existing Stage-A trajectories.
- Updated N=64/96/128 resolution comparison for SC-IIb candidates.
- Real-data development regression: 273 natural pairs across 13 certified
  carriers, zero provisional candidates under frozen gates.
- Native C++ physics kernel unchanged.
