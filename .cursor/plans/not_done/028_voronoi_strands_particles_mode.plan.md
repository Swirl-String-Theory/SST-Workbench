---
name: Voronoi strands particles mode
overview: Keep Voronoi multi-pass; per-path mode/size on FilamentPath; one kindSpec() via const int IDs (no KIND_* macros, no _M kinds); black bg; Image particles vs RGB strands.
todos:
  - id: common-filpath-unify
    content: "FilamentPath: mode, particleSize, strandWidth; const int kinds + kindSpec(); drop KIND_* #defines and all _M; black BG"
    status: pending
  - id: image-strands
    content: "Image: per-path particleSize glow; RGB strands use per-path strandWidth"
    status: pending
  - id: catalog-readme
    content: Mirror FilamentPath fields + kindSpec (no _M) in Python/tests; README kit H
    status: pending
isProject: true
---

# Voronoi: per-path mode/size + one kind table

## Locked

- No `#define KIND_*`. Names are `const int`; geometry only in `kindSpec()`.
- Delete all `KIND_*_M`. Flip later is `q = -q`, not a second ID.
- `FilamentPath` has `mode`, `particleSize`, `strandWidth`.
- Black bg; even paths particles, odd RGB strands.

See Cursor plan `voronoi_strands_particles_mode_a1a9dac5`.
