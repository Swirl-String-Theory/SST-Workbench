# Audit of supplied Codex v0.2.2 code + evidence

The supplied bundle was treated as historical parent evidence, not reinterpreted as a
successful physics result.

Key supported conclusions from its own machine-readable summaries:

- six preregistered realization-level atlas draws from three construction lineages;
- parents were historically available, so this is not an unseen-parent or statistically
  independent external atlas;
- four candidates passed resolution, temporal and core robustness gates;
- S37 mesh-gauge qualification: 0/4;
- S40 long, S50 RPO/Floquet, S60 mechanism and trefoil Phase B were therefore not executed
  on eligible trajectories;
- overall physics verdict remained INDETERMINATE;
- causal language remained unauthorized.

The bundle already used SST Knot Library v0.2.3 for parent loading/braid generation, but it
hard-coded that path and maintained separate source/topology declarations. v0.3.1 replaces
that partial integration with a pinned, hashed KnotRecord dependency contract.

A separate versioning defect was also found in the supplied code: project metadata reported
0.2.2 while `sst_seed_falsifier.__version__` and native setup still reported 0.2.0, and some
batch banners reported v0.2.1. v0.3.1 has one release identity (`RELEASE.json`, Python
runtime version, packaging metadata and batch banners).
